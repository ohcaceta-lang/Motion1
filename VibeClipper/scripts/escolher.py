"""VibeClipper, etapa 2 (escolhe): prepara a escolha dos melhores momentos (quem escolhe é o Claude, seguindo o SKILL.md).

  python scripts/escolher.py preparar trabalho/transcricao.json --saida trabalho/transcricao-numerada.md
      -> a transcrição INTEIRA em frases numeradas (L0001 [0:12:34] texto), pro Claude ler do começo ao fim,
         e trabalho/escolha.modelo.json, o formato que o Claude preenche (trabalho/escolha.json).

  python scripts/escolher.py validar trabalho/escolha.json --transcricao trabalho/transcricao.json --saida trabalho/cortes.json
      -> confere cada corte (hook na 1ª frase, termina na conclusão, 30 a 75 s), ajusta o início e o fim na palavra exata
         (pelo timestamp do Whisper), ordena pela nota (o melhor primeiro) e grava o cortes.json que as outras etapas usam.

  python scripts/escolher.py resumo trabalho/cortes.json --saida saida/cortes.md
      -> o resumo pra postar: cada corte com título, duração, nota, legenda pra postar e o arquivo (o melhor primeiro).

O que o Claude preenche por corte (escolha.json):
  titulo, legenda (pra postar), nota (0 a 10), porque, hook_tipo (fato surpreendente | afirmação ousada | começo de história),
  linha_ini (a frase do HOOK), linha_fim (a frase da CONCLUSÃO), pular_ini / cortar_fim (palavras a tirar da 1ª/última
  frase, opcional), enrolacao (as linhas logo antes do hook que ele pulou, ex. "L0410-L0413", opcional) e enfase (as
  palavras que mais importam, que a legenda destaca).
"""
import argparse
import json
import os
import re
import sys

FIM_FRASE = re.compile(r"[.!?…]['\")»]*$")


def palavras_de(transcricao):
    return [w for s in transcricao["segmentos"] for w in s["palavras"]]


def frases(pal, pausa=0.8, max_pal=45):
    """Agrupa as palavras em frases: corta na pontuação final, numa pausa longa ou em 45 palavras."""
    linhas, atual = [], []
    for i, w in enumerate(pal):
        atual.append(i)
        prox = pal[i + 1] if i + 1 < len(pal) else None
        fim = (FIM_FRASE.search(w["p"]) or prox is None or (prox["ini"] - w["fim"]) >= pausa or len(atual) >= max_pal)
        if fim:
            linhas.append(atual)
            atual = []
    return linhas


def hms(s):
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{int(s % 60):02d}"


def preparar(arq_tr, saida, titulo=None):
    tr = json.load(open(arq_tr, encoding="utf-8"))
    pal = palavras_de(tr)
    ls = frases(pal)
    out = [f"# Transcrição numerada{': ' + titulo if titulo else ''}", "",
           f"{len(ls)} frases, {len(pal)} palavras, {tr['duracao'] / 60:.0f} min. Formato: `Lnnnn [h:mm:ss] texto`.",
           "Leia do começo ao fim e preencha o escolha.json (veja o SKILL.md, etapa 2).", ""]
    mapa = []
    for k, idx in enumerate(ls, 1):
        w0, w1 = pal[idx[0]], pal[idx[-1]]
        out.append(f"L{k:04d} [{hms(w0['ini'])}] " + " ".join(pal[i]["p"] for i in idx))
        mapa.append({"linha": f"L{k:04d}", "p_ini": idx[0], "p_fim": idx[-1], "ini": w0["ini"], "fim": w1["fim"]})
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    open(saida, "w", encoding="utf-8").write("\n".join(out) + "\n")
    base = os.path.dirname(os.path.abspath(saida))
    json.dump(mapa, open(os.path.join(base, "linhas.json"), "w", encoding="utf-8"), ensure_ascii=False)
    modelo = {"cor_marca": None, "cortes": [{
        "titulo": "título curto do corte", "legenda": "a legenda pra postar junto (sem hashtag)", "nota": 0.0,
        "porque": "por que funciona sozinho pra um estranho", "hook_tipo": "fato surpreendente",
        "linha_ini": "L0000", "pular_ini": 0, "linha_fim": "L0000", "cortar_fim": 0,
        "enrolacao": "L0000-L0000", "enfase": ["palavra", "outra"]}]}
    json.dump(modelo, open(os.path.join(base, "escolha.modelo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[escolher] {len(ls)} frases -> {saida} (+ linhas.json, escolha.modelo.json)")


def _linha(mapa, nome):
    for m in mapa:
        if m["linha"] == nome:
            return m
    raise SystemExit(f"[escolher] linha {nome} não existe")


def _norm(p):
    return re.sub(r"[^\w%$]", "", p.lower())


def corrigir(rel, correcoes):
    """Troca na legenda o que o Whisper ouviu errado (nome próprio, número quebrado), mantendo o tempo do trecho.
    correcoes = [["o que o Whisper escreveu", "o que foi dito"], ...]"""
    feitas = []
    for de, para in correcoes:
        alvo = [_norm(x) for x in de.split()]
        ns = [_norm(w["p"]) for w in rel]
        for i in range(len(ns) - len(alvo) + 1):
            if ns[i:i + len(alvo)] == alvo:
                t0, t1 = rel[i]["ini"], rel[i + len(alvo) - 1]["fim"]
                novas = para.split()
                passo = (t1 - t0) / len(novas)
                rel[i:i + len(alvo)] = [{"p": p, "ini": round(t0 + k * passo, 3), "fim": round(t0 + (k + 1) * passo, 3)}
                                        for k, p in enumerate(novas)]
                feitas.append([de, para])
                break
    return rel, feitas


def validar(arq_esc, arq_tr, saida, dur_min=30, dur_max=75):
    tr = json.load(open(arq_tr, encoding="utf-8"))
    pal = palavras_de(tr)
    base = os.path.dirname(os.path.abspath(arq_tr))
    arq_mapa = os.path.join(base, "linhas.json")
    if not os.path.exists(arq_mapa):
        raise SystemExit("[escolher] rode antes: escolher.py preparar (ele grava o linhas.json)")
    mapa = json.load(open(arq_mapa, encoding="utf-8"))
    esc = json.load(open(arq_esc, encoding="utf-8"))
    cortes, avisos = [], []
    for c in esc["cortes"]:
        a, b = _linha(mapa, c["linha_ini"]), _linha(mapa, c["linha_fim"])
        i0 = a["p_ini"] + int(c.get("pular_ini", 0))
        i1 = b["p_fim"] - int(c.get("cortar_fim", 0))
        ant = pal[i0 - 1]["fim"] if i0 > 0 else 0.0
        prox = pal[i1 + 1]["ini"] if i1 + 1 < len(pal) else pal[i1]["fim"] + 1.0
        ini = max(pal[i0]["ini"] - 0.12, (ant + pal[i0]["ini"]) / 2)        # começa no hook, sem pegar a palavra anterior
        fim = min(pal[i1]["fim"] + 0.35, max(pal[i1]["fim"] + 0.08, (pal[i1]["fim"] + prox) / 2))
        dur = fim - ini
        if not dur_min <= dur <= dur_max:
            avisos.append(f"'{c['titulo']}' tem {dur:.1f} s (fora de {dur_min} a {dur_max} s)")
        rel = [{"p": w["p"], "ini": round(w["ini"] - ini, 3), "fim": round(w["fim"] - ini, 3)} for w in pal[i0:i1 + 1]]
        rel, feitas = corrigir(rel, c.get("correcoes", []))
        if len(feitas) < len(c.get("correcoes", [])):
            avisos.append(f"'{c['titulo']}': correção não achada ({[x for x in c['correcoes'] if x not in feitas]})")
        item = {k: v for k, v in c.items() if k not in ("linha_ini", "linha_fim", "pular_ini", "cortar_fim", "enrolacao", "hook_ate")}
        item.update({"ini": round(ini, 3), "fim": round(fim, 3), "dur": round(dur, 2),
                     "linhas": f"{c['linha_ini']}-{c['linha_fim']}",
                     "hook": " ".join(w["p"] for w in rel if w["fim"] <= _linha(mapa, c.get("hook_ate", c["linha_ini"]))["fim"] - ini + 0.01),
                     "conclusao": " ".join(w["p"] for w in rel if w["ini"] >= max(b["ini"], pal[i0]["ini"]) - ini - 0.01),
                     "palavras": rel})
        if c.get("enrolacao"):
            e0, e1 = (c["enrolacao"].split("-") + [c["enrolacao"]])[:2]
            ma, mb = _linha(mapa, e0), _linha(mapa, e1)
            item["enrolacao"] = {"texto": " ".join(w["p"] for w in pal[ma["p_ini"]:mb["p_fim"] + 1]),
                                 "ini": round(ma["ini"], 2), "fim": round(mb["fim"], 2)}
        cortes.append(item)
    cortes.sort(key=lambda c: -float(c.get("nota", 0)))                    # o melhor sempre vem primeiro
    for n, c in enumerate(cortes, 1):
        c["n"] = n
    out = {"cor_marca": esc.get("cor_marca"), "cortes": [{"n": c.pop("n"), **c} for c in cortes]}
    if os.path.exists(saida):                                               # guarda o que outras etapas já gravaram
        velho = json.load(open(saida, encoding="utf-8"))
        out = {**{k: v for k, v in velho.items() if k != "cortes"}, **out}
    json.dump(out, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in out["cortes"]:
        print(f"[escolher] {c['n']}. {c['titulo']} | {c['dur']:.1f} s | nota {c['nota']} | {hms(c['ini'])}")
    for a in avisos:
        print("[escolher] AVISO:", a, file=sys.stderr)
    return out


def resumo(arq_cortes, saida, pasta_videos=None):
    """O resumo pra postar: cada corte com título, duração, nota, legenda pra postar e o arquivo (o melhor primeiro)."""
    d = json.load(open(arq_cortes, encoding="utf-8"))
    pasta_videos = pasta_videos or os.path.dirname(os.path.abspath(saida))
    cor = d.get("cor_video", {}).get("cor") or d.get("cor_marca")
    out = ["# Cortes prontos pra postar", "", "O melhor vem primeiro.", ""]
    if cor:
        out += [f"Cor de destaque da legenda: {cor}" + (f" ({d['cor_video']['origem']})" if d.get("cor_video") else ""), ""]
    for c in d["cortes"]:
        arq = os.path.join(pasta_videos, f"corte-{c['n']}.mp4")
        m, s = divmod(int(round(c["dur"])), 60)
        out += [f"## {c['n']}. {c['titulo']}", "",
                f"- Duração: {m}:{s:02d} | Nota: {c.get('nota')} | Hook: {c.get('hook_tipo', '')}",
                f"- Arquivo: {os.path.basename(arq)}" + ("" if os.path.exists(arq) else " (ainda não renderizado)"),
                f"- No vídeo original: {hms(c['ini'])} a {hms(c['fim'])}", "",
                "Legenda pra postar:", "", c.get("legenda", ""), ""]
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    open(saida, "w", encoding="utf-8").write("\n".join(out))
    print(f"[escolher] resumo com {len(d['cortes'])} cortes -> {saida}")


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar")
    p.add_argument("transcricao")
    p.add_argument("--saida", required=True)
    p.add_argument("--titulo", default=None)
    v = sub.add_parser("validar")
    v.add_argument("escolha")
    v.add_argument("--transcricao", required=True)
    v.add_argument("--saida", required=True)
    v.add_argument("--min", type=float, default=30)
    v.add_argument("--max", type=float, default=75)
    r = sub.add_parser("resumo")
    r.add_argument("cortes")
    r.add_argument("--saida", required=True)
    a = ap.parse_args()
    if a.cmd == "preparar":
        preparar(a.transcricao, a.saida, a.titulo)
    elif a.cmd == "resumo":
        resumo(a.cortes, a.saida)
    else:
        validar(a.escolha, a.transcricao, a.saida, a.min, a.max)


if __name__ == "__main__":
    main()
