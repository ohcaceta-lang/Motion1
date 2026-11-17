"""VibeClipper, etapa 3 (corta): enquadra o corte na vertical (9:16) e planeja os zooms.

  python scripts/enquadrar.py trabalho/corte-1/fonte.mp4 --cortes trabalho/cortes.json --n 1 --saida trabalho/corte-1/plano.json

O que faz:
  1. Detecta cada troca de câmera (cena) pela diferença entre quadros seguidos.
  2. Em cada cena, acha o rosto com a detecção de rosto (YuNet do OpenCV; sem o modelo, cai no Haar que vem no OpenCV).
     Se tem duas pessoas no quadro, fica com quem está falando (a boca que mais se mexe).
  3. Centraliza a moldura 9:16 em quem está na tela, PARADA dentro da cena (sem tremer), e recentraliza a cada troca de câmera:
     ninguém fica cortado pela metade e a câmera nunca fica num lugar sem alguém falando. Se a pessoa se inclina mais do que a
     moldura aguenta, a moldura acompanha só o necessário, devagar. No close de perfil, centra na cabeça (olhos x nariz).
  4. Lê a transcrição (o tempo de cada palavra) e marca um zoom suave no FIM de uma frase, a cada poucos segundos
     (1,0 -> ~1,2 e volta), sempre em volta do rosto e com o rosto inteiro dentro do quadro.

O renderizar.py usa o plano.json (função `moldura(plano, t)`).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO_ROSTO = "face_detection_yunet_2023mar.onnx"
FIM_FRASE = re.compile(r"[.!?…]['\")»]*$")


def achar_modelo():
    for d in (os.environ.get("VIBECLIPPER_MODELOS", ""), os.path.join(AQUI, "..", "modelos"),
              os.path.join(os.path.expanduser("~"), ".cache", "vibeclipper")):
        p = os.path.join(d, MODELO_ROSTO)
        if d and os.path.exists(p):
            return os.path.abspath(p)
    return None


def info_video(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", arq],
                       capture_output=True, text=True)
    d = json.loads(r.stdout)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den), float(d["format"]["duration"])


class Detector:
    def __init__(self, w, h):
        self.modelo = achar_modelo()
        import cv2
        self.cv2 = cv2
        if self.modelo:
            self.yn = cv2.FaceDetectorYN.create(self.modelo, "", (w, h), 0.6, 0.3, 5000)
            self.tipo = "YuNet (OpenCV)"
        else:
            base = cv2.data.haarcascades
            self.haar = cv2.CascadeClassifier(base + "haarcascade_frontalface_default.xml")
            self.perfil = cv2.CascadeClassifier(base + "haarcascade_profileface.xml")
            self.tipo = "Haar (OpenCV, sem o modelo YuNet)"

    def rostos(self, bgr):
        """Lista de (x, y, w, h, confiança, virada) em pixels do quadro dado. virada = x do meio dos olhos - x do nariz
        (positivo: olhando pra esquerda, a nuca fica à direita)."""
        if self.modelo:
            _, f = self.yn.detect(bgr)
            return [] if f is None else [(float(a[0]), float(a[1]), float(a[2]), float(a[3]), float(a[-1]),
                                          float((a[4] + a[6]) / 2 - a[8])) for a in f]
        g = self.cv2.cvtColor(bgr, self.cv2.COLOR_BGR2GRAY)
        out = [(*map(float, r), 0.8, 0.0) for r in self.haar.detectMultiScale(g, 1.1, 6, minSize=(40, 40))]
        if not out:
            out = [(*map(float, r), 0.7, 0.0) for r in self.perfil.detectMultiScale(g, 1.1, 6, minSize=(40, 40))]
            fl = self.cv2.flip(g, 1)
            out += [(g.shape[1] - x - w, y, w, h, 0.7, 0.0) for x, y, w, h in
                    map(lambda r: tuple(map(float, r)), self.perfil.detectMultiScale(fl, 1.1, 6, minSize=(40, 40)))]
        return out


def analisar(arq, fps=30, larg=960, a_cada=6):
    """Uma passada no vídeo: diferença entre quadros (cenas) + rostos a cada `a_cada` quadros + movimento da boca."""
    W, H, _, dur = info_video(arq)
    alt = int(round(larg * H / W / 2) * 2)
    det = Detector(larg, alt)
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", arq, "-vf", f"fps={fps},scale={larg}:{alt}:flags=area",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=larg * alt * 3 * 4)
    tam = larg * alt * 3
    difs, amostras, ant, k = [], [], None, 0
    caixas = []                                                               # rostos da última detecção (px)
    while True:
        b = p.stdout.read(tam)
        if len(b) < tam:
            break
        q = np.frombuffer(b, np.uint8).reshape(alt, larg, 3)
        peq = q[::6, ::6].astype(np.int16)
        difs.append(0.0 if ant is None else float(np.abs(peq - ant[::6, ::6]).mean()))
        if k % a_cada == 0:
            caixas = det.rostos(q)
            amostras.append({"k": k, "t": k / fps, "rostos": []})
            for x, y, w, h, s, vir in caixas:
                tx0, tx1 = int(max(0, x - w * 0.2)), int(min(larg, x + w * 1.2))  # roupa logo abaixo do queixo
                ty0, ty1 = int(min(alt - 1, y + h * 1.25)), int(min(alt, y + h * 2.0))
                roupa = q[ty0:ty1, tx0:tx1].reshape(-1, 3).mean(0).tolist() if ty1 > ty0 and tx1 > tx0 else [0, 0, 0]
                amostras[-1]["rostos"].append([x / larg, y / alt, w / larg, h / alt, s, 0.0, roupa, vir / larg])
        if ant is not None and amostras and caixas:                          # boca = metade de baixo do rosto, quadro a quadro
            for j, (x, y, w, h, s, _) in enumerate(caixas):
                y0, y1 = int(max(0, y + h * 0.55)), int(min(alt, y + h * 1.0))
                x0, x1 = int(max(0, x + w * 0.2)), int(min(larg, x + w * 0.8))
                if y1 > y0 and x1 > x0:
                    amostras[-1]["rostos"][j][5] += float(np.abs(q[y0:y1, x0:x1].astype(np.int16) - ant[y0:y1, x0:x1]).mean())
        ant = q.astype(np.int16)
        k += 1
    p.wait()
    return {"W": W, "H": H, "fps": fps, "n": k, "dur": k / fps, "difs": difs, "amostras": amostras, "detector": det.tipo}


def cenas_de(difs, fps, minimo=0.25):
    d = np.array(difs)
    med = np.median(d[d > 0]) if (d > 0).any() else 1.0
    lim = max(14.0, 5.0 * med)
    cortes = [0]
    for i in range(1, len(d)):
        if d[i] > lim and (i - cortes[-1]) / fps >= minimo:
            cortes.append(i)
    cortes.append(len(d))
    return [(cortes[i] / fps, cortes[i + 1] / fps) for i in range(len(cortes) - 1)], lim


def trilhas_da_cena(amostras, t0, t1):
    """Liga os rostos de quadro em quadro (o mesmo rosto anda pouco a cada 0,2 s): cada trilha é uma pessoa."""
    trilhas = []
    for a in amostras:
        if not (t0 + 0.05 <= a["t"] < t1 - 0.05):
            continue
        usadas = set()
        for x, y, w, h, s, m, roupa, vir in sorted(a["rostos"], key=lambda r: -r[2] * r[3]):
            if h < 0.06:                                                       # rosto minúsculo (foto, fundo)
                continue
            cx = x + w / 2
            melhor = None
            for k, tr in enumerate(trilhas):
                if k in usadas:
                    continue
                dt = a["t"] - tr["t"][-1]
                passo = max(0.06, 0.6 * tr["w"][-1]) * max(1.0, dt / 0.2)
                if dt <= 1.0 and abs(cx - tr["cx"][-1]) < passo and 0.6 < w / tr["w"][-1] < 1.6:
                    if melhor is None or abs(cx - tr["cx"][-1]) < abs(cx - trilhas[melhor]["cx"][-1]):
                        melhor = k
            if melhor is None:
                trilhas.append({"t": [], "cx": [], "w": [], "it": [], "roupas": []})
                melhor = len(trilhas) - 1
            tr = trilhas[melhor]
            usadas.add(melhor)
            tr["t"].append(a["t"]); tr["cx"].append(cx); tr["w"].append(w)
            tr["it"].append((x, y, w, h, s, m, vir)); tr["roupas"].append(roupa)
    return trilhas


def alvo_da_cena(amostras, t0, t1, roupa_ant=None):
    """A pessoa da cena: a trilha principal (mais tempo na tela e maior). Se tem duas pessoas grandes no quadro (plano
    aberto), fica com quem fala: a boca que mais se mexe; se a diferença é pequena, com quem estava na tela antes (a roupa)."""
    grupos = trilhas_da_cena(amostras, t0, t1)
    if not grupos:
        return None
    n_am = max(1, sum(1 for a in amostras if t0 + 0.05 <= a["t"] < t1 - 0.05))
    for g in grupos:
        it = np.array(g["it"])
        g["freq"] = len(it) / n_am
        g["area"] = float(np.median(it[:, 2] * it[:, 3]))
        g["boca"] = float(np.mean(it[:, 5]))
        g["roupa"] = np.mean(np.array(g["roupas"]), axis=0)
        g["peso"] = g["freq"] * math.sqrt(g["area"])
    grupos.sort(key=lambda g: -g["peso"])
    fortes = [g for g in grupos if g["freq"] >= 0.5 and g["area"] >= 0.5 * grupos[0]["area"]]
    criterio = "rosto principal"
    if len(fortes) >= 2:                                                      # duas pessoas: fica com quem fala
        fortes.sort(key=lambda g: -g["boca"])
        razao = fortes[0]["boca"] / max(fortes[1]["boca"], 1e-6)
        escolhido, criterio = fortes[0], f"{len(fortes)} rostos, quem fala (boca {razao:.1f}x)"
        if razao < 1.35 and roupa_ant is not None:                           # boca empatada: continuidade
            escolhido = min(fortes, key=lambda g: float(np.abs(g["roupa"] - roupa_ant).sum()))
            criterio = f"{len(fortes)} rostos, boca empatada ({razao:.1f}x): a mesma pessoa da cena anterior"
    else:
        escolhido = grupos[0]
    it = np.array(escolhido["it"])
    x, y, w, h = (float(np.median(it[:, i])) for i in range(4))
    return {"face": [x, y, w, h], "virada": float(np.median(it[:, 6])), "espalhamento": float(np.std(escolhido["cx"])),
            "rostos": len(grupos), "criterio": criterio, "roupa": escolhido["roupa"],
            "trilha": list(zip(escolhido["t"], escolhido["cx"]))}


def caminho_da_moldura(trilha, a, b, W, cw, fw_px, desvio_px):
    """Moldura PARADA na cena quando a pessoa cabe nela inteira; se a pessoa anda mais do que isso (se inclina, levanta),
    a moldura só acompanha o necessário, devagar, pra ela nunca sair do quadro. Devolve (x0 fixo, None) ou (None, pontos)."""
    folga = max(cw / 2 - 0.75 * fw_px - abs(desvio_px), 0.05 * cw)          # o quanto o rosto anda sem chegar na borda
    alvo = [(t, cx * W + desvio_px) for t, cx in trilha]
    if not alvo:
        return None, None
    xs = [p for _, p in alvo]
    if max(xs) - min(xs) <= 2 * folga + 40:                                   # cabe parado: centra no meio do movimento
        c = (max(xs) + min(xs)) / 2
        return min(max(c - cw / 2, 0), W - cw), None
    c, seg = xs[0], []
    for t, p in alvo:                                                         # acompanha só o que passar da folga
        if p - c > folga:
            c = p - folga
        elif c - p > folga:
            c = p + folga
        seg.append(c)
    k = 3                                                                     # média de ~0,6 s pra mexer suave
    sv = [float(np.mean(seg[max(0, i - k // 2):i + k // 2 + 1])) for i in range(len(seg))]
    pts = [[round(t, 3), round(min(max(v - cw / 2, 0), W - cw), 1)] for (t, _), v in zip(alvo, sv)]
    pts = [[round(a, 3), pts[0][1]]] + pts + [[round(b, 3), pts[-1][1]]]
    return None, pts


def pontos_de_zoom(palavras, cenas, espaco=3.2, max_vazio=6.5, margem_ini=1.0, margem_fim=0.8):
    """Fim de frase (pontuação ou pausa) a cada poucos segundos, longe das trocas de câmera."""
    cand = []
    for i, w in enumerate(palavras):
        prox = palavras[i + 1]["ini"] if i + 1 < len(palavras) else None
        pausa = (prox - w["fim"]) if prox is not None else 0
        if prox is None:
            continue
        forca = 2 if FIM_FRASE.search(w["p"]) else (1 if (w["p"].endswith(",") and pausa >= 0.2) or pausa >= 0.35 else 0)
        cand.append((w["fim"], forca, pausa))

    def cena_de(t):
        for i, (a, b) in enumerate(cenas):
            if a <= t < b:
                return i, a, b
        return None, 0, 0

    validos = [(t, f, p) for t, f, p in cand
               if (lambda c: c[0] is not None and t - c[1] >= margem_ini and c[2] - t >= margem_fim)(cena_de(t))]
    # 1) fins de frase de verdade (ponto final), um a cada `espaco` segundos no mínimo
    esc = []
    for t, f, _ in validos:
        if f == 2 and (not esc or t - esc[-1] >= espaco):
            esc.append(t)
    # 2) trecho longo sem zoom: completa com a pausa (vírgula, respiro) mais perto do meio do vazio; se a fala é corrida,
    #    sem pontuação nem pausa (live, conversa), usa a maior respirada perto do meio, pra nunca ficar muito tempo sem zoom
    fim_total = palavras[-1]["fim"] if palavras else 0
    mudou = True
    while mudou:
        mudou = False
        marcos = [0.0] + esc + [fim_total]
        for a, b in zip(marcos, marcos[1:]):
            if b - a <= max_vazio:
                continue
            meio = (a + b) / 2
            ops = [(t, f, p) for t, f, p in validos if t - a >= espaco and b - t >= espaco * 0.8 and t not in esc]
            fortes = [x for x in ops if x[1] >= 1]
            if fortes:
                esc.append(min(fortes, key=lambda x: abs(x[0] - meio))[0])
            elif ops:
                miolo = [x for x in ops if abs(x[0] - meio) <= (b - a) / 4] or ops
                esc.append(max(miolo, key=lambda x: x[2])[0])
            else:
                continue
            esc.sort()
            mudou = True
            break
    return [round(t, 3) for t in esc]


def planejar(arq, palavras, zoom=1.2, dur_zoom=0.45):
    an = analisar(arq)
    W, H = an["W"], an["H"]
    cenas, lim = cenas_de(an["difs"], an["fps"])
    cw = H * 9 / 16
    ct = []
    roupa_ant = None
    for a, b in cenas:
        alvo = alvo_da_cena(an["amostras"], a, b, roupa_ant)
        if alvo is not None:
            roupa_ant = alvo["roupa"]
        if alvo is None:                                                      # sem rosto: centro do quadro
            alvo = {"face": [0.5 - 0.05, 0.3, 0.1, 0.18], "espalhamento": 0, "rostos": 0, "criterio": "sem rosto: centro"}
        fx, fy, fw, fh = alvo["face"]
        desvio = 0.0
        if fw * W > 0.45 * cw:                                                # close: centra na CABEÇA, não só no rosto
            desvio = max(-0.15 * fw, min(0.15 * fw, 1.0 * alvo.get("virada", 0.0)))   # de perfil, a nuca fica do outro lado
        trilha = alvo.get("trilha") or [((a + b) / 2, fx + fw / 2)]
        x0, caminho = caminho_da_moldura(trilha, a, b, W, cw, fw * W, desvio * W)
        # zoom máximo que ainda deixa o rosto inteiro dentro do quadro, com folga (o zoom é em volta do centro do rosto)
        cy = fy + fh / 2
        zmax = min(0.85 * cw / (fw * W), (cy - 0.03) / max(cy - fy, 1e-3), (0.97 - cy) / max(fh / 2, 1e-3), 1.35)
        cena = {"ini": round(a, 3), "fim": round(b, 3), "face": [round(v, 4) for v in alvo["face"]],
                "zmax": round(zmax, 3), "rostos": alvo["rostos"], "criterio": alvo["criterio"],
                "espalhamento": round(alvo["espalhamento"], 4)}
        if caminho is None:
            cena.update({"x0": round(x0, 1), "x_min": round(x0, 1), "x_max": round(x0, 1)})
        else:
            xs = [p[1] for p in caminho]
            cena.update({"x0": round(min(xs), 1), "x_min": round(min(xs), 1), "x_max": round(max(xs), 1),
                         "caminho": caminho, "rosto_cx": [[round(t, 3), round(v, 4)] for t, v in trilha],
                         "criterio": alvo["criterio"] + "; a pessoa se mexe: a moldura acompanha devagar"})
        ct.append(cena)
    pts = pontos_de_zoom(palavras, cenas)
    zooms, nivel, cena_ant = [], 1.0, None
    for t in pts:
        i = next(k for k, c in enumerate(ct) if c["ini"] <= t < c["fim"])
        if i != cena_ant:
            nivel, cena_ant = 1.0, i
        close = ct[i]["face"][2] * W > 0.45 * cw
        z_alvo = min(min(zoom, 1.12) if close else zoom, ct[i]["zmax"])          # no close o zoom é mais leve
        if z_alvo < 1.06:
            continue
        para = z_alvo if nivel == 1.0 else 1.0
        zooms.append({"t": t, "de": round(nivel, 3), "para": round(para, 3), "dur": dur_zoom, "cena": i})
        nivel = para
    return {"fonte": os.path.basename(arq), "W": W, "H": H, "fps": an["fps"], "dur": round(an["dur"], 3),
            "detector": an["detector"], "limiar_cena": round(lim, 2), "moldura_w": round(cw, 1),
            "cenas": ct, "zooms": zooms, "trocas_de_camera": [c["ini"] for c in ct[1:]]}


def _suave(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def zoom_em(plano, t):
    cena = next((c for c in plano["cenas"] if c["ini"] <= t < c["fim"]), plano["cenas"][-1])
    i = plano["cenas"].index(cena)
    z = 1.0
    for e in plano["zooms"]:
        if e["cena"] != i or e["t"] > t:
            continue
        z = e["de"] + (e["para"] - e["de"]) * _suave((t - e["t"]) / e["dur"])
    return cena, z


def x0_em(cena, t):
    """O x da moldura (pixels da fonte) no tempo t: fixo, ou o caminho suave da cena."""
    if "caminho" not in cena:
        return cena["x0"]
    c = np.array(cena["caminho"])
    return float(np.interp(t, c[:, 0], c[:, 1]))


def moldura(plano, t, sem_zoom=False):
    """Retângulo (x, y, w, h) em pixels da fonte pra o tempo t: moldura 9:16 da cena + zoom em volta do rosto."""
    W, H, cw = plano["W"], plano["H"], plano["moldura_w"]
    cena, z = zoom_em(plano, t)
    if sem_zoom:
        z = 1.0
    x0 = x0_em(cena, t)
    fx, fy, fw, fh = cena["face"]
    fcx = fx + fw / 2
    if "rosto_cx" in cena:
        r = np.array(cena["rosto_cx"])
        fcx = float(np.interp(t, r[:, 0], r[:, 1]))
    px = min(max(fcx * W, x0 + 0.1 * cw), x0 + 0.9 * cw)                    # o ponto fixo do zoom = centro do rosto
    py = min(max((fy + fh / 2) * H, 0), H)
    x = px + (x0 - px) / z
    y = py + (0 - py) / z
    return x, y, cw / z, H / z, z


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fonte")
    ap.add_argument("--cortes", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--zoom", type=float, default=1.2)
    a = ap.parse_args()
    c = next(c for c in json.load(open(a.cortes, encoding="utf-8"))["cortes"] if c["n"] == a.n)
    pl = planejar(a.fonte, c["palavras"], a.zoom)
    json.dump(pl, open(a.saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[enquadrar] corte {a.n}: {len(pl['cenas'])} cenas, trocas em {pl['trocas_de_camera']}, "
          f"{len(pl['zooms'])} zooms em {[z['t'] for z in pl['zooms']]} ({pl['detector']})")


if __name__ == "__main__":
    main()
