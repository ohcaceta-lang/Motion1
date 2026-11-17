"""VibeClipper, etapa 4 (edita): os efeitos sonoros do corte (os arquivos de som que vêm dentro da skill, em sons/).

  python scripts/efeitos.py --plano trabalho/corte-1/plano.json --legenda trabalho/corte-1/legenda.json \
                            --saida trabalho/corte-1/sfx.json [--sem]

  - whoosh.wav em cada zoom que entra e whoosh-2.wav em cada zoom que sai (o pico do whoosh cai no meio do movimento);
  - pop.wav, baixinho, quando uma palavra de destaque aparece na legenda (no máximo um a cada 6 s, nunca colado num whoosh);
  - --sem: corte sem efeito sonoro (grava a lista vazia).
O renderizar.py mistura esses sons por baixo do áudio original.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
SONS = os.path.normpath(os.path.join(AQUI, "..", "sons"))


def pico(arq):
    """Segundos até o ponto mais forte do som (pra alinhar o pico com o movimento)."""
    b = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", arq, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                       capture_output=True).stdout
    a = np.abs(np.frombuffer(b, np.float32))
    env = np.convolve(a, np.ones(80) / 80, "same")
    return float(env.argmax() / 8000) if len(env) else 0.0


def planejar(plano, legenda=None, ganho_whoosh=-5.0, ganho_pop=-10.0):
    sfx = []
    p_in, p_out = pico(os.path.join(SONS, "whoosh.wav")), pico(os.path.join(SONS, "whoosh-2.wav"))
    for z in plano["zooms"]:
        entra = z["para"] > z["de"]
        arq, pk = ("whoosh.wav", p_in) if entra else ("whoosh-2.wav", p_out)
        sfx.append({"t": round(max(0.0, z["t"] + z["dur"] / 2 - pk), 3), "som": arq, "ganho_db": ganho_whoosh,
                    "motivo": "zoom entra" if entra else "zoom sai"})
    if legenda:
        ult = -99.0
        p_pop = pico(os.path.join(SONS, "pop.wav"))
        for g in legenda["grupos"]:
            if not g["enfase"]:
                continue
            t = g["ini"]
            perto = any(abs((s["t"]) - t) < 0.7 for s in sfx if s["som"] != "pop.wav")
            if t - ult >= 6.0 and not perto and t > 0.3:
                sfx.append({"t": round(max(0.0, t - p_pop), 3), "som": "pop.wav", "ganho_db": ganho_pop,
                            "motivo": "destaque: " + " ".join(g["enfase"])})
                ult = t
    return sorted(sfx, key=lambda s: s["t"])


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--legenda", default=None)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--sem", action="store_true", help="sem efeito sonoro")
    a = ap.parse_args()
    plano = json.load(open(a.plano, encoding="utf-8"))
    leg = json.load(open(a.legenda, encoding="utf-8")) if a.legenda and os.path.exists(a.legenda) else None
    sfx = [] if a.sem else planejar(plano, leg)
    json.dump({"pasta_sons": SONS, "sons": sfx}, open(a.saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[efeitos] {len(sfx)} sons: " + ", ".join(f"{s['som']}@{s['t']:.1f}" for s in sfx) if sfx else "[efeitos] sem som")


if __name__ == "__main__":
    main()
