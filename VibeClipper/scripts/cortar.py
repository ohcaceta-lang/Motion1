"""VibeClipper, etapa 3 (corta): corta cada momento escolhido do vídeo original, na palavra exata.

  python scripts/cortar.py --cortes trabalho/cortes.json --trechos trabalho/trechos --audio trabalho/audio.m4a \
                           --pasta trabalho [--cru trabalho/cru --antes 3]

Pra cada corte:
  - acha onde o trecho baixado começa no vídeo original (alinha o som do trecho com o áudio inteiro, ao centésimo de
    segundo), porque o YouTube entrega o trecho começando no quadro-chave mais perto;
  - grava trabalho/corte-N/fonte.mp4: o 16:9 na resolução máxima, 30 fps, do HOOK (1ª palavra) até a CONCLUSÃO;
  - com --cru, grava também o momento cru no vídeo original (1080p, com alguns segundos antes do hook) e um .json com o
    tempo do hook dentro dele, pra comparar o original com o corte pronto.
Se você já tem o vídeo inteiro no computador, passe --video arquivo.mp4 no lugar de --trechos.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

import numpy as np

SR = 8000


def audio(arq, ini=0.0, dur=None):
    c = ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0, ini):.3f}", "-i", arq]
    if dur:
        c += ["-t", f"{dur:.3f}"]
    c += ["-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(c, capture_output=True, check=True).stdout, np.float32)


def alinhar(trecho, audio_inteiro, aprox, busca=45.0, janela=20.0):
    """Tempo (no vídeo original) do início do trecho, por correlação do som."""
    a = audio(trecho, 1.0, janela)
    b0 = max(0.0, aprox - busca)
    b = audio(audio_inteiro, b0, janela + 2 * busca + 1)
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    cc = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)[: len(b) - len(a)]
    k = int(np.argmax(cc))
    conf = float(cc[k] / len(a))
    return b0 + k / SR - 1.0, conf


def enc_video(alta=True):
    """h264 na placa NVIDIA se tiver (rápido); senão libx264."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if "h264_nvenc" in r:
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "16" if alta else "19", "-b:v", "0"]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "14" if alta else "18"]


def tem_audio(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                        arq], capture_output=True, text=True)
    return bool(r.stdout.strip())


def cortar(fonte, ini, dur, saida, largura=None, fps=30, audio_extra=None, audio_off=0.0):
    """Corta [ini, ini+dur] da fonte. Com o áudio inteiro do vídeo (audio_extra), o som sai dele, alinhado (o som que vem
    no trecho baixado em HLS é de qualidade baixa e só serve pra achar o alinhamento)."""
    vf = f"fps={fps}" + (f",scale={largura}:-2:flags=lanczos" if largura else "")
    entradas = ["-ss", f"{ini:.3f}", "-i", fonte]
    mapa = []
    if audio_extra:
        entradas += ["-ss", f"{ini + audio_off:.3f}", "-i", audio_extra]
        mapa = ["-map", "0:v:0", "-map", "1:a:0"]
    c = ["ffmpeg", "-nostdin", "-v", "error", "-y", *entradas, "-t", f"{dur:.3f}", *mapa, "-vf", vf,
         *enc_video(largura is None), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-movflags", "+faststart", saida]
    subprocess.run(c, check=True)


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cortes", required=True)
    ap.add_argument("--pasta", required=True)
    ap.add_argument("--trechos", default=None)
    ap.add_argument("--video", default=None)
    ap.add_argument("--audio", default=None, help="o áudio inteiro (pra alinhar os trechos)")
    ap.add_argument("--cru", default=None, help="pasta do momento cru 16:9 (1080p)")
    ap.add_argument("--antes", type=float, default=3.0)
    ap.add_argument("--n", type=int, default=None, help="só esse corte")
    a = ap.parse_args()
    todos = json.load(open(a.cortes, encoding="utf-8"))
    for c in todos["cortes"]:
        if a.n and c["n"] != a.n:
            continue
        if a.video:
            fonte, off, conf = a.video, 0.0, 1.0
        else:
            cand = sorted(glob.glob(os.path.join(a.trechos, f"corte-{c.get('trecho', c['n'])}.*")))
            if not cand:
                raise SystemExit(f"[cortar] falta o trecho do corte {c['n']} (rode baixar.py --trechos)")
            fonte = cand[0]
            off, conf = alinhar(fonte, a.audio, c.get("trecho_ini_pedido", c["ini"] - 5))
        c["trecho_ini"] = round(off, 3)
        pasta = os.path.join(a.pasta, f"corte-{c['n']}")
        os.makedirs(pasta, exist_ok=True)
        cortar(fonte, c["ini"] - off, c["dur"], os.path.join(pasta, "fonte.mp4"), audio_extra=a.audio, audio_off=off)
        msg = f"[cortar] corte {c['n']}: trecho começa em {off:.2f} s (confiança {conf:.2f}), fonte.mp4 com {c['dur']:.1f} s"
        if a.cru:
            os.makedirs(a.cru, exist_ok=True)
            ini_cru = max(0.0, c["ini"] - a.antes - off)
            cortar(fonte, ini_cru, c["dur"] + (c["ini"] - off - ini_cru), os.path.join(a.cru, f"corte-{c['n']}.mp4"),
                   largura=1920, audio_extra=a.audio, audio_off=off)
            info = {"n": c["n"], "titulo": c.get("titulo"), "video_ini": round(ini_cru + off, 3),
                    "hook_em": round(c["ini"] - off - ini_cru, 3), "hook": c.get("hook"),
                    "corte_termina_em": round(c["dur"] + (c["ini"] - off - ini_cru), 3), "conclusao": c.get("conclusao")}
            if c.get("enrolacao"):
                e = c["enrolacao"]
                info["enrolacao"] = {"texto": e["texto"], "ini": round(e["ini"] - off - ini_cru, 3),
                                     "fim": round(e["fim"] - off - ini_cru, 3)}
            json.dump(info, open(os.path.join(a.cru, f"corte-{c['n']}.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            msg += f", cru com o hook em {info['hook_em']:.2f} s"
        print(msg)
    json.dump(todos, open(a.cortes, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
