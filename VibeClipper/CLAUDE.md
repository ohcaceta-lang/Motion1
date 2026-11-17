# VibeClipper

Esta pasta é a skill VibeClipper: ela corta um vídeo longo do YouTube em cortes verticais prontos pra postar. O passo a passo
está no `SKILL.md` e a explicação pra pessoa no `README.md`.

## Quando pedirem pra configurar
("configura esse repositório inteiro pra mim", "faça sua mágica", "instala tudo")
1. Rode `python instalar.py` aqui nesta pasta (no Mac e no Linux pode ser `python3`). Ele confere o computador e instala o que
   falta: as bibliotecas do Python, o deno que o yt-dlp usa, as bibliotecas da placa NVIDIA, o detector de rosto e a fonte.
2. Se faltar o **Python** (3.10 ou mais novo): no Windows `winget install --id Python.Python.3.12 -e`, no Mac
   `brew install python`, no Linux `sudo apt install python3 python3-venv`. No Windows, se o comando `python` ainda não aparecer
   depois de instalar, use o caminho completo (`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`).
3. Se faltar o **ffmpeg**, o `instalar.py` diz o comando (no Windows `winget install --id Gyan.FFmpeg -e`, no Mac
   `brew install ffmpeg`, no Linux `sudo apt install ffmpeg`). Instale e rode o `instalar.py` de novo: os scripts acham o
   ffmpeg recém-instalado sozinhos, sem precisar reabrir nada.
4. Termina quando aparecer **"A configuração terminou: o VibeClipper está pronto pra usar."** Diga isso pra pessoa e mostre o
   prompt de uso: `Roda a skill do VibeClipper nesse vídeo <link do YouTube>`.

Não apague nem mude nada fora desta pasta (a não ser instalar o Python, o ffmpeg e as bibliotecas).

## Quando pedirem pra cortar um vídeo
("Roda a skill do VibeClipper nesse vídeo <link>", "corta esse vídeo")
Siga o `SKILL.md` desta pasta do começo ao fim, sem perguntar nada, a não ser que falte o link. Se a configuração ainda não foi
feita, faça ela antes (acima).

## Python
Se existir a pasta `.venv` aqui (o `instalar.py` cria quando o Python do sistema não deixa instalar biblioteca), use o Python
dela em todos os comandos: `.venv/Scripts/python` no Windows, `.venv/bin/python` no Mac e no Linux.
