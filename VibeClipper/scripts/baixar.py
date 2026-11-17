"""VibeClipper, etapas 1 (assiste) e 3 (corta): baixa o vídeo do YouTube com o yt-dlp (sem login, sem cookie).

Dois modos:
  1) tudo pra assistir:  python scripts/baixar.py <link> --pasta trabalho
       -> trabalho/info.json (título, canal, duração), trabalho/miniatura.jpg, trabalho/audio.m4a (pra transcrever)
          e, só se pedir --video 720, o vídeo inteiro leve em trabalho/video-720p.mp4 (a skill não precisa dele)
  2) só os trechos escolhidos, na melhor qualidade (até 4K), pro recorte vertical sair nítido:
       python scripts/baixar.py <link> --pasta trabalho --trechos trabalho/cortes.json [--folga 5] [--altura 2160]
       -> trabalho/trechos/corte-N.mp4 (do início do corte - folga até o fim + folga)

Só baixa o que você tem direito de usar (o seu canal, ou com autorização do dono).
"""
import argparse
import json
import os
import subprocess
import sys
import time


def yt(args, log=None, tentativas=3, espera=30):
    """Roda o yt-dlp; se a rede cair, espera e tenta de novo (até `tentativas` vezes)."""
    cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-progress", "--retries", "5", *args]
    for k in range(1, tentativas + 1):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if log:
            with open(log, "a", encoding="utf-8") as f:
                f.write(" ".join(cmd) + "\n" + r.stdout + r.stderr + "\n")
        if r.returncode == 0:
            return r
        if k < tentativas:
            print(f"[baixar] falhou (tentativa {k} de {tentativas}), tentando de novo em {espera} s", file=sys.stderr)
            time.sleep(espera)
    raise SystemExit(f"[baixar] yt-dlp falhou {tentativas} vezes:\n{r.stderr[-1500:]}\n"
                     "Dica: o YouTube muda direto e o yt-dlp acompanha. Atualize e tente de novo: "
                     f'"{sys.executable}" -m pip install --upgrade "yt-dlp[default,deno]"')


def duracao(arq):
    if not os.path.exists(arq):
        return 0.0
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def hms(s):
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:06.3f}"


def baixar_tudo(url, pasta, video=None):
    os.makedirs(pasta, exist_ok=True)
    log = os.path.join(pasta, "baixar.log")
    base = os.path.join(pasta, "video")
    yt(["--skip-download", "--write-info-json", "--write-thumbnail", "--convert-thumbnails", "jpg", "-o", base, url], log)
    os.replace(base + ".info.json", os.path.join(pasta, "info.json"))
    if os.path.exists(base + ".jpg"):
        os.replace(base + ".jpg", os.path.join(pasta, "miniatura.jpg"))
    yt(["-f", "bestaudio[ext=m4a]/bestaudio", "-o", os.path.join(pasta, "audio.%(ext)s"), url], log)
    if video:
        yt(["-f", f"bv*[height<={video}][vcodec^=avc1]/bv*[height<={video}]", "-o",
            os.path.join(pasta, f"video-{video}p.%(ext)s"), url], log)
    info = json.load(open(os.path.join(pasta, "info.json"), encoding="utf-8"))
    audio = next((os.path.join(pasta, f) for f in sorted(os.listdir(pasta)) if f.startswith("audio.")
                  and not f.endswith((".part", ".ytdl"))), None)
    print(f"[baixar] {info.get('title')} | {info.get('channel')} | {info.get('duration_string')} -> {pasta}")
    print(f"[baixar] áudio pra transcrever: {os.path.normpath(audio) if audio else None}")


def baixar_trechos(url, pasta, arq_cortes, folga=5.0, altura=2160):
    """Baixa SÓ os trechos dos cortes (com folga antes e depois), na melhor qualidade até `altura`."""
    cortes = json.load(open(arq_cortes, encoding="utf-8"))["cortes"]
    dest = os.path.join(pasta, "trechos")
    os.makedirs(dest, exist_ok=True)
    log = os.path.join(pasta, "baixar.log")
    # HLS (m3u8) primeiro: o ffmpeg pula direto pro segmento do trecho. No DASH (webm/mp4 inteiro) o pulo pro meio de um
    # vídeo de 2 horas pode travar. O som do trecho serve só pra alinhar; o corte usa o audio.m4a inteiro (melhor qualidade).
    fmt = (f"bv*[height<={altura}][protocol^=m3u8]+ba[protocol^=m3u8]/bv*[height<={altura}][protocol^=m3u8]+ba/"
           f"bv*[height<={altura}]+ba/b[height<={altura}]")
    for c in cortes:
        antes = folga
        if c.get("enrolacao"):                                  # guarda também a enrolação que o Claude pulou (pro antes e depois)
            antes = max(folga, c["ini"] - c["enrolacao"]["ini"] + 2)
        ini, fim = c["ini"] - antes, c["fim"] + folga
        saida = os.path.join(dest, f"corte-{c['n']}")
        esperado = fim - max(0.0, ini)
        pronto = os.path.join(dest, f"corte-{c['n']}.mp4")
        if os.path.exists(pronto) and duracao(pronto) >= esperado - 3:
            print(f"[baixar] corte {c['n']}: já baixado")
            c["trecho_ini_pedido"] = round(max(0.0, ini), 3)
            continue
        for f in os.listdir(dest):                                          # sobra quebrada de uma tentativa anterior
            if f.startswith(f"corte-{c['n']}."):
                os.remove(os.path.join(dest, f))
        for k in range(3):
            yt(["-f", fmt, "--merge-output-format", "mp4", "--download-sections", f"*{hms(ini)}-{hms(fim)}",
                "-o", saida + ".%(ext)s", url], log)
            if duracao(pronto) >= esperado - 3:
                break
            print(f"[baixar] corte {c['n']}: arquivo incompleto, baixando de novo", file=sys.stderr)
            if os.path.exists(pronto):
                os.remove(pronto)
            time.sleep(20)
        else:
            raise SystemExit(f"[baixar] corte {c['n']}: não consegui baixar o trecho inteiro")
        print(f"[baixar] corte {c['n']}: {hms(ini)} a {hms(fim)} ({duracao(pronto):.1f} s)")
        c["trecho_ini_pedido"] = round(max(0.0, ini), 3)
    json.dump({**json.load(open(arq_cortes, encoding="utf-8")), "cortes": cortes},
              open(arq_cortes, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--pasta", required=True)
    ap.add_argument("--video", type=int, default=None, help="baixa também o vídeo inteiro nessa altura (ex.: 720)")
    ap.add_argument("--trechos", default=None, help="cortes.json: baixa só os trechos escolhidos")
    ap.add_argument("--folga", type=float, default=5.0)
    ap.add_argument("--altura", type=int, default=2160)
    a = ap.parse_args()
    if a.trechos:
        baixar_trechos(a.url, a.pasta, a.trechos, a.folga, a.altura)
    else:
        baixar_tudo(a.url, a.pasta, a.video)


if __name__ == "__main__":
    main()
