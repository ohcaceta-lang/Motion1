"""Força a skill google-flow-skill-v1 (BRPLia) a abrir o Google Flow em espanhol.

Por quê: a conta do usuário está em português e o Flow abre em PT ("Novo projeto"),
mas a skill procura os textos em espanhol/inglês ("Proyecto nuevo", "Longitud", "Vídeo"...).
Uso (na pasta da skill, no PC do usuário):  python patch_idioma.py
Rodar de novo sempre que baixar a skill de novo. É idempotente.
"""
from pathlib import Path

LANG = '"--lang=es-419"'
URL_OLD = '"https://labs.google/fx/es-419/tools/flow"'
URL_NEW = '"https://flow.google.com/?hl=es-419"'
VIEW = 'viewport={"width": 1280, "height": 900},'
VIEW_NEW = 'viewport={"width": 1280, "height": 900}, locale="es-419",'


def patch(path, pairs):
    p = Path(path)
    if not p.exists():
        print(f"{path}: não encontrado, pulando")
        return
    txt = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if new in txt:
            continue
        n = txt.count(old)
        txt = txt.replace(old, new)
        print(f"{path}: {n} troca(s) -> {new[:45]}")
    p.write_text(txt, encoding="utf-8")


patch("flow_provider/browser.py", [
    ('"--disable-blink-features=AutomationControlled"]',
     '"--disable-blink-features=AutomationControlled", ' + LANG + ']'),
    (VIEW, VIEW_NEW),
])
patch("flow.py", [
    ('args=["--disable-blink-features=AutomationControlled"]',
     'args=["--disable-blink-features=AutomationControlled", ' + LANG + ']'),
    (VIEW, VIEW_NEW),
    (URL_OLD, URL_NEW),
])
patch("flow_provider/project.py", [
    (URL_OLD, URL_NEW),
    ('r"Proyecto nuevo|Nuevo proyecto|New project"',
     'r"Proyecto nuevo|Nuevo proyecto|New project|Novo projeto"'),
])
patch("diag.py", [
    ('args=["--disable-blink-features=AutomationControlled"]',
     'args=["--disable-blink-features=AutomationControlled", ' + LANG + ']'),
    ('viewport={"width": 1280, "height": 900})',
     'viewport={"width": 1280, "height": 900}, locale="es-419")'),
    ('"https://labs.google/fx/es-419/tools/flow"', URL_NEW),
])
print("Pronto.")
