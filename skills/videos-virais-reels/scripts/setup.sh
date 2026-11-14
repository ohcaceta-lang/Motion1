#!/usr/bin/env bash
# Prepara uma pasta de projeto de vídeo: copia os scripts e instala fontes/emojis/dependências.
# uso: bash setup.sh /caminho/do/projeto
set -e
P="${1:?informe a pasta do projeto}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$P/assets"
cp "$HERE"/lib.js "$HERE"/render.js "$HERE"/synth.py "$HERE"/tighten.py "$HERE"/mixar.py "$HERE"/buscar_em_alta.py "$HERE"/buscar_fotos.py "$P/"
cp "$HERE/../assets/template.html" "$P/video.html"
cd "$P"
[ -f package.json ] || npm init -y >/dev/null
npm i --silent @fontsource/playfair-display @fontsource/anton @fontsource/special-elite @fontsource/caveat @fontsource/dm-serif-display @twemoji/svg >/dev/null 2>&1
python3 -c "import scipy" 2>/dev/null || pip install -q scipy 2>/dev/null
python3 -c "import numpy, scipy; print('python ok')"
node -e "require('playwright'); console.log('playwright ok')"
echo "projeto pronto em $P"
