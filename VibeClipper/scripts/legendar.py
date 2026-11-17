"""VibeClipper, etapa 4 (edita): a legenda do corte (arquivo .ass que o renderizar.py queima no vídeo).

  python scripts/legendar.py --cortes trabalho/cortes.json --n 1 --plano trabalho/corte-1/plano.json \
                             --saida trabalho/corte-1/legenda.ass [--cor "#1E6BFF"] [--fonte trabalho]

  - Só 2 ou 3 palavras na tela por vez (fácil de acompanhar, melhora a retenção), em CAIXA ALTA, fonte forte, branca com
    contorno preto, no terço de baixo e sempre ABAIXO do rosto.
  - Cada grupo aparece e some no tempo exato das palavras (o timestamp do Whisper).
  - As palavras de ênfase (as que o Claude marcou no escolha.json, e os números) ganham a cor de destaque.
  - A cor: 1) a que você pedir (--cor); 2) a cor da marca do criador (cor_marca no escolha.json); 3) se não tiver nenhuma,
    ele puxa do próprio vídeo uma cor forte que combina com a identidade dele (função cor_do_video) e anota de onde tirou.
    Por padrão olha os trechos de todos os cortes (trabalho/corte-*/fonte.mp4), espalhados pelo vídeo; --fonte troca isso
    por outro vídeo, pasta ou padrão (ex.: o vídeo inteiro, se você já tem ele no computador). A cor sai uma vez só e fica
    gravada no cortes.json: a mesma em todos os cortes.
  - A fonte da legenda é copiada pra pasta do corte (fontes/), assim o render acha ela em qualquer disco.
"""
import argparse
import colorsys
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

import numpy as np

FIM_FRASE = re.compile(r"[.!?…]['\")»]*$")
LARG, ALT = 1080, 1920

FONTES = ["Montserrat-Black.ttf", "Montserrat-ExtraBold.ttf", "Poppins-Black.ttf", "Poppins-ExtraBold.ttf",
          "ariblk.ttf", "Arial Black.ttf", "impact.ttf", "Impact.ttf", "arialbd.ttf", "Arial Bold.ttf"]


def pastas_de_fonte():
    h = os.path.expanduser("~")
    return [os.path.join(h, ".cache", "vibeclipper", "fontes"),                 # a Montserrat que o instalar.py baixa
            os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
            "/Library/Fonts", os.path.join(h, "Library", "Fonts"), "/System/Library/Fonts/Supplemental",
            "/usr/share/fonts/truetype", os.path.join(h, ".local", "share", "fonts"), os.path.join(h, ".fonts")]


def nome_familia(caminho):
    """Nome da família como o libass procura (name ID 1 da tabela 'name', ex.: 'Montserrat Black')."""
    import struct
    d = open(caminho, "rb").read()
    try:
        for i in range(struct.unpack(">H", d[4:6])[0]):
            tag, _, off, _ = struct.unpack(">4sIII", d[12 + 16 * i:28 + 16 * i])
            if tag == b"name":
                _, cnt, so = struct.unpack(">HHH", d[off:off + 6])
                for j in range(cnt):
                    pid, _, _, nid, ln, o = struct.unpack(">HHHHHH", d[off + 6 + 12 * j:off + 18 + 12 * j])
                    if pid == 3 and nid == 1:
                        return d[off + so + o:off + so + o + ln].decode("utf-16-be")
    except struct.error:
        pass
    from PIL import ImageFont
    return ImageFont.truetype(caminho, 10).getname()[0]


def achar_fonte(pedida=None):
    """Caminho e nome da família de uma fonte forte instalada (Montserrat Black de preferência)."""
    nomes = ([pedida] if pedida else []) + FONTES
    for nome in nomes:
        if nome and os.path.isfile(nome):
            return nome, nome_familia(nome)
        for d in pastas_de_fonte():
            for raiz, _, arqs in os.walk(d) if os.path.isdir(d) else []:
                if nome in arqs:
                    p = os.path.join(raiz, nome)
                    return p, nome_familia(p)
    raise SystemExit("[legendar] nenhuma fonte forte encontrada; instale a Montserrat (grátis) ou passe --fonte-arquivo")


def normal(p):
    p = unicodedata.normalize("NFC", p.lower())
    return re.sub(r"[^\w%$]", "", p)


def hex_ass(hexcor, alfa=0):
    hexcor = hexcor.lstrip("#")
    r, g, b = int(hexcor[0:2], 16), int(hexcor[2:4], 16), int(hexcor[4:6], 16)
    return f"&H{alfa:02X}{b:02X}{g:02X}{r:02X}"


def videos_de(itens):
    """Os vídeos de onde tirar a cor: arquivo, padrão (corte-*/fonte.mp4) ou pasta de trabalho (pega os corte-*/fonte.mp4)."""
    out = []
    for it in itens:
        if os.path.isdir(it):
            out += sorted(glob.glob(os.path.join(it, "corte-*", "fonte.mp4"))) or sorted(glob.glob(os.path.join(it, "*.mp4")))
        elif any(ch in it for ch in "*?["):
            out += sorted(glob.glob(it))
        elif os.path.exists(it):
            out.append(it)
    return list(dict.fromkeys(out))


def duracao(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def cor_do_video(arqs, n=24):
    """Uma cor forte da identidade do vídeo: matiz mais presente entre os pixels saturados e claros (luz do cenário, marca,
    objetos), em quadros espalhados pelo vídeo (ou pelos trechos dos cortes). Devolve o hex já ajustado pra legenda (viva e
    clara) e de onde veio."""
    if isinstance(arqs, str):
        arqs = [arqs]
    fontes = [(a, duracao(a)) for a in arqs]
    fontes = [(a, d) for a, d in fontes if d > 0]
    if not fontes:
        return "#FFD400", "não achei vídeo pra olhar: amarelo padrão"
    por_video = -(-n // len(fontes))
    quadros = [(a, d * (j + 0.5) / por_video) for a, d in fontes for j in range(por_video)]
    hs, pix = [], []
    for arq, t in quadros:
        b = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.2f}", "-i", arq, "-frames:v", "1", "-vf",
                            "scale=320:-2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if not b:
            continue
        q = np.frombuffer(b, np.uint8).reshape(-1, 3).astype(np.float32) / 255
        mx, mn = q.max(1), q.min(1)
        s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        sel = q[(s > 0.65) & (mx > 0.5)]          # só cor forte de verdade (luz, marca), fora a pele
        for r, g, bb in sel[:: max(1, len(sel) // 400)]:
            h, _, _ = colorsys.rgb_to_hsv(r, g, bb)
            hs.append(h); pix.append((r, g, bb))
    if not hs:
        return "#FFD400", "o vídeo não tem cor forte: amarelo padrão"
    hist, bordas = np.histogram(hs, bins=24, range=(0, 1))
    k = int(np.argmax(hist))
    sel = [p for h, p in zip(hs, pix) if bordas[k] <= h < bordas[k + 1]]
    r, g, b = np.median(np.array(sel), axis=0)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    bruto = "#%02X%02X%02X" % tuple(int(round(c * 255)) for c in (r, g, b))
    r2, g2, b2 = colorsys.hsv_to_rgb(h, max(s, 0.78), max(v, 0.98))     # viva e clara pra ler sobre o vídeo
    final = "#%02X%02X%02X" % tuple(int(round(c * 255)) for c in (r2, g2, b2))
    return final, (f"matiz mais presente nos pixels saturados de {len(quadros)} quadros do vídeo ({hist[k] / max(1, sum(hist)):.0%} "
                   f"deles, cor média {bruto}, matiz {h * 360:.0f} graus), clareada pra legenda")


def grupos_de(palavras, max_pal=3, max_chars=17, pausa=0.32):
    gs, at = [], []
    for i, w in enumerate(palavras):
        at.append(w)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        txt = " ".join(x["p"] for x in at)
        fecha = (prox is None or len(at) >= max_pal or FIM_FRASE.search(w["p"]) or
                 (w["p"].endswith(",") and len(at) >= 2) or (prox["ini"] - w["fim"]) > pausa or
                 (len(at) >= 2 and len(txt + " " + prox["p"]) > max_chars))
        if fecha:
            gs.append(at)
            at = []
    # junta palavra sozinha curta com o vizinho quando não tem pausa no meio
    out = []
    for g in gs:
        if out and len(g) == 1 and len(out[-1]) < max_pal and g[0]["ini"] - out[-1][-1]["fim"] < 0.15 and \
                not FIM_FRASE.search(out[-1][-1]["p"]) and len(" ".join(x["p"] for x in out[-1] + g)) <= max_chars + 3:
            out[-1] = out[-1] + g
        else:
            out.append(g)
    return out


def marcar_enfase(palavras, enfase):
    alvos = [[normal(x) for x in e.split()] for e in enfase]
    ns = [normal(w["p"]) for w in palavras]
    marca = [False] * len(palavras)
    for a in alvos:
        if not a:
            continue
        for i in range(len(ns) - len(a) + 1):
            if ns[i:i + len(a)] == a:
                for j in range(i, i + len(a)):
                    marca[j] = True
    for i, w in enumerate(palavras):                                       # números sempre em destaque
        if re.search(r"\d", w["p"]):
            marca[i] = True
    return marca


def limpar(p):
    return re.sub(r"[,;:.…]+$", "", p).upper().replace("{", "(").replace("}", ")")


def tempo_ass(s):
    s = max(0.0, s)
    cs = int(round(s * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def legenda(corte, plano, cor, fonte_arq, fonte_nome, tam=100, y_base=0.68):
    from PIL import ImageFont
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from enquadrar import moldura
    pal = corte["palavras"]
    fim_total = corte["dur"]
    pal = [w for w in pal if w["ini"] < fim_total]
    marca = marcar_enfase(pal, corte.get("enfase", []))
    for w, m in zip(pal, marca):
        w["_enf"] = m
    gs = grupos_de(pal)
    fnt = ImageFont.truetype(fonte_arq, tam)
    linhas = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {LARG}", f"PlayResY: {ALT}", "WrapStyle: 2",
              "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
              "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
              "MarginR, MarginV, Encoding",
              f"Style: Corte,{fonte_nome},{tam},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,1,0,1,7,3,5,"
              "40,40,0,1", "", "[Events]",
              "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    eventos = []
    cor_ass = hex_ass(cor)
    for i, g in enumerate(gs):
        ini = g[0]["ini"]
        prox = gs[i + 1][0]["ini"] if i + 1 < len(gs) else None
        fim = prox if (prox is not None and prox - g[-1]["fim"] < 0.45) else g[-1]["fim"] + 0.18
        fim = min(fim, fim_total)
        if fim - ini < 0.12:
            fim = ini + 0.12
        texto = " ".join(limpar(w["p"]) for w in g)
        larg = fnt.getlength(texto) + 14 * len(g)
        fs = tam if larg <= 960 else int(tam * 960 / larg)
        # posição: terço de baixo, e sempre abaixo do queixo
        y = y_base * ALT
        for tt in (ini, (ini + fim) / 2, fim - 0.01):
            x0, y0, w0, h0, _ = moldura(plano, tt)
            cena = next((c for c in plano["cenas"] if c["ini"] <= tt < c["fim"]), plano["cenas"][-1])
            fy, fh = cena["face"][1], cena["face"][3]
            queixo = ((fy + fh * 1.12) * plano["H"] - y0) / h0 * ALT
            y = max(y, queixo + fs * 0.75 + 24)
        y = min(y, ALT * 0.80)
        partes = []
        for w in g:
            t = limpar(w["p"])
            partes.append("{\\c" + cor_ass + "&}" + t + "{\\c&H00FFFFFF&}" if w["_enf"] else t)
        anim = "{\\an5\\pos(%d,%d)\\fs%d\\fscx86\\fscy86\\t(0,90,\\fscx100\\fscy100)}" % (LARG // 2, int(y), fs)
        linhas.append(f"Dialogue: 0,{tempo_ass(ini)},{tempo_ass(fim)},Corte,,0,0,0,,{anim}{' '.join(partes)}")
        eventos.append({"ini": round(ini, 3), "fim": round(fim, 3), "texto": texto, "y": int(y), "fs": fs,
                        "enfase": [limpar(w["p"]) for w in g if w["_enf"]]})
    return "\n".join(linhas) + "\n", eventos


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cortes", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--fonte", nargs="*", default=None,
                    help="de onde tirar a cor, se precisar: vídeo(s), padrão ou pasta (padrão: os trechos de todos os cortes)")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--cor", default=None, help="cor de destaque pedida, ex.: #1E6BFF")
    ap.add_argument("--fonte-arquivo", default=None, help="arquivo .ttf/.otf da fonte da legenda")
    a = ap.parse_args()
    todos = json.load(open(a.cortes, encoding="utf-8"))
    corte = next(c for c in todos["cortes"] if c["n"] == a.n)
    plano = json.load(open(a.plano, encoding="utf-8"))
    if a.cor:
        cor, origem = a.cor, "pedida no prompt"
    elif todos.get("cor_marca"):
        cor, origem = todos["cor_marca"], "cor da marca do criador"
    elif todos.get("cor_video"):                                           # já tirada do vídeo: a mesma pra todos os cortes
        cor, origem = todos["cor_video"]["cor"], todos["cor_video"]["origem"]
    else:
        pasta_corte = os.path.dirname(os.path.abspath(a.saida))
        videos = videos_de(a.fonte or [os.path.dirname(pasta_corte)]) or videos_de([pasta_corte])
        cor, origem = cor_do_video(videos, n=48)
        todos["cor_video"] = {"cor": cor, "origem": origem, "videos": [os.path.basename(os.path.dirname(v)) + "/" +
                                                                       os.path.basename(v) for v in videos]}
        json.dump(todos, open(a.cortes, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    farq, fnome = achar_fonte(a.fonte_arquivo)
    pasta_fontes = os.path.join(os.path.dirname(os.path.abspath(a.saida)), "fontes")   # a fonte vai junto do corte
    os.makedirs(pasta_fontes, exist_ok=True)
    copia = os.path.join(pasta_fontes, os.path.basename(farq))
    if os.path.abspath(farq) != os.path.abspath(copia):
        shutil.copyfile(farq, copia)
    ass, ev = legenda(corte, plano, cor, copia, fnome)
    open(a.saida, "w", encoding="utf-8").write(ass)
    meta = {"cor": cor, "origem_cor": origem, "fonte": os.path.basename(farq), "fonte_nome": fnome,
            "pasta_fonte": pasta_fontes, "grupos": ev}
    json.dump(meta, open(os.path.splitext(a.saida)[0] + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[legendar] corte {a.n}: {len(ev)} legendas, cor {cor} ({origem}), fonte {fnome}")


if __name__ == "__main__":
    main()
