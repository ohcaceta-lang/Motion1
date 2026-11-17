"""VibeClipper, etapa 4 (edita): renderiza o corte final na vertical, em 1080p (1080x1920, Full HD), 30 fps, H.264 + AAC.

  python scripts/renderizar.py --fonte trabalho/corte-1/fonte.mp4 --plano trabalho/corte-1/plano.json \
        --legenda trabalho/corte-1/legenda.ass --sfx trabalho/corte-1/sfx.json --saida saida/corte-1.mp4
  python scripts/renderizar.py --fonte ... --plano ... --saida saida/corte-1-cru.mp4 --cru     (só cortado e enquadrado)

  - a moldura 9:16 de cada cena e os zooms em volta do rosto vêm do plano.json (enquadrar.py), quadro a quadro, sem tremer;
  - a legenda .ass (legendar.py) é queimada por cima;
  - o áudio original é normalizado (-14 LUFS, o padrão dos Shorts/Reels) e os efeitos (efeitos.py) entram por baixo;
  - usa a placa NVIDIA (h264_nvenc) se tiver; senão libx264.
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from enquadrar import moldura  # noqa: E402

LARG, ALT, FPS = 1080, 1920, 30


def enc_video():
    from comum import nvenc_funciona
    if nvenc_funciona():
        return ["-c:v", "h264_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "19", "-b:v", "12M",
                "-maxrate", "20M", "-bufsize", "24M", "-profile:v", "high"]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high"]


def faixa(plano):
    """A faixa vertical que o decodificador já recorta (fixa em cada cena): a moldura 9:16 mais o quanto ela anda na cena."""
    W = plano["W"]
    anda = max(c.get("x_max", c["x0"]) - c.get("x_min", c["x0"]) for c in plano["cenas"])
    bw = min(W, int(round(plano["moldura_w"] + anda)) // 2 * 2 + 4)
    xs = [min(max(int(c.get("x_min", c["x0"])), 0), W - bw) for c in plano["cenas"]]
    return bw, xs


def caminho_filtro(p, base):
    """Caminho pro filtro ass do ffmpeg: relativo à pasta de saída (sem o "C:" que o filtro entende errado); se estiver em
    outro disco, absoluto com o ":" escapado."""
    try:
        r = os.path.relpath(p, base)
    except ValueError:
        r = os.path.abspath(p)
    return r.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def x_por_cena(plano, xs):
    """Expressão do ffmpeg com o x da faixa de cada cena."""
    exp = str(xs[-1])
    for c, x in zip(reversed(plano["cenas"][:-1]), reversed(xs[:-1])):
        exp = f"if(lt(t\\,{c['fim']:.4f})\\,{x}\\,{exp})"
    return exp


def renderizar(fonte, plano, saida, legenda=None, sfx=None, cru=False, ate=None):
    import cv2
    W, H = plano["W"], plano["H"]
    bw, xs = faixa(plano)
    dur = min(plano["dur"], ate) if ate else plano["dur"]
    nq = int(round(dur * FPS))
    dec = ["ffmpeg", "-nostdin", "-v", "error", "-i", fonte, "-t", f"{dur:.3f}", "-vf",
           f"fps={FPS},crop={bw}:{H}:'{x_por_cena(plano, xs)}':0", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    pasta = os.path.dirname(os.path.abspath(saida))
    os.makedirs(pasta, exist_ok=True)
    vf = "null"
    if legenda and not cru:
        meta = os.path.splitext(legenda)[0] + ".json"
        fontsdir = json.load(open(meta, encoding="utf-8"))["pasta_fonte"] if os.path.exists(meta) else None
        vf = f"ass='{caminho_filtro(legenda, pasta)}'" + (f":fontsdir='{caminho_filtro(fontsdir, pasta)}'" if fontsdir else "")
    entradas = ["-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{LARG}x{ALT}", "-r", str(FPS), "-i", "-",
                "-i", os.path.abspath(fonte)]
    sons = []
    if sfx and not cru:
        d = json.load(open(sfx, encoding="utf-8"))
        sons = [s for s in d["sons"] if s["t"] < dur]
        for s in sons:
            entradas += ["-i", os.path.join(d["pasta_sons"], s["som"])]
    voz = "[1:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000"
    if sons:
        fc = [f"{voz}[voz]"]
        for i, s in enumerate(sons):
            ms = int(round(s["t"] * 1000))
            fc.append(f"[{i + 2}:a]aresample=48000,volume={s['ganho_db']}dB,adelay={ms}|{ms}[s{i}]")
        fc.append("[voz]" + "".join(f"[s{i}]" for i in range(len(sons))) +
                  f"amix=inputs={len(sons) + 1}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    else:
        fc = [f"{voz},alimiter=limit=0.95[a]"]
    fc.append(f"[0:v]{vf},format=yuv420p[v]")
    enc = ["ffmpeg", "-nostdin", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(fc), "-map", "[v]",
           "-map", "[a]", "-t", f"{dur:.3f}", *enc_video(), "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", os.path.basename(saida)]
    pd = subprocess.Popen(dec, stdout=subprocess.PIPE, bufsize=bw * H * 3 * 2)
    pe = subprocess.Popen(enc, stdin=subprocess.PIPE, cwd=pasta)
    tam = bw * H * 3
    t0 = time.time()
    k = 0
    while k < nq:
        b = pd.stdout.read(tam)
        if len(b) < tam:
            break
        q = np.frombuffer(b, np.uint8).reshape(H, bw, 3)
        t = k / FPS
        x, y, w, h, _ = moldura(plano, t, sem_zoom=cru)
        ic = next((i for i, c in enumerate(plano["cenas"]) if c["ini"] <= t < c["fim"]), len(plano["cenas"]) - 1)
        x0 = xs[ic]
        s = LARG / w
        m = np.float32([[s, 0, -(x - x0) * s], [0, s, -y * s]])
        out = cv2.warpAffine(q, m, (LARG, ALT), flags=cv2.INTER_LINEAR if s < 1 else cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
        pe.stdin.write(out.tobytes())
        k += 1
    pe.stdin.close()
    pe.wait()
    pd.stdout.close()
    pd.wait()
    if pe.returncode != 0:
        raise SystemExit(f"[renderizar] o ffmpeg falhou ({saida})")
    print(f"[renderizar] {saida}: {k} quadros ({k / FPS:.1f} s) em {time.time() - t0:.0f} s"
          f"{' (cru)' if cru else ''}, {len(sons)} efeitos")


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fonte", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--legenda", default=None)
    ap.add_argument("--sfx", default=None)
    ap.add_argument("--cru", action="store_true", help="só cortado e enquadrado: sem zoom, sem legenda, sem efeito")
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()
    plano = json.load(open(a.plano, encoding="utf-8"))
    renderizar(a.fonte, plano, a.saida, a.legenda, a.sfx, a.cru, a.ate)


if __name__ == "__main__":
    main()
