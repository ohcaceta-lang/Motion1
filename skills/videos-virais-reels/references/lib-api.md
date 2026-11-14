# API do motor de animação (`lib.js`)

A página HTML tem 720×1280 e é exportada em 1080×1920. Tudo é **determinístico**: `renderAt(t)` desenha o
quadro do instante `t`, e o `render.js` tira um screenshot por quadro e envia para o ffmpeg.
Não use `setTimeout`, transições CSS ou `Date`: todo movimento tem de ser função de `t`.

Ordem dos scripts na página: `assets/words.js` (define `window.WORDS`) → `lib.js` → o seu script → `finalize(...)`.

## Tempo e easing
- `prog(t, a, b)`: progresso de 0 a 1 entre `a` e `b` (com clamp).
- Easings: `easeOut`, `easeIn`, `easeInOut`, `easeOutExpo`, `backOut` (overshoot).
- `pop(t, t0, d=0.35)`: escala com overshoot a partir de `t0` (é 0 antes de `t0`).
- `lerp(a, b, p)`, `clamp(v)`, `mix(corA, corB, p)` (cores em hex).

## Narração
- `ws(i)` / `we(i)`: início e fim da palavra `i` da narração (índices de `window.WORDS`, já sem as entradas ".").
- **Amarre cortes de cena e animações a `ws(i)`**, nunca a segundos fixos: se a voz for trocada, tudo continua sincronizado.
- Para encontrar os índices, imprima a lista: `python3 -c "import json;[print(i,d['w'],d['s']) for i,d in enumerate(json.load(open('assets/voz_edit.json')))]"`.

## Estrutura
- `scene(inicio, fim, fundoCSS, zoom=0.02)` → `s`: um container visível só em `[inicio, fim)`, com zoom lento automático.
  `s.updates.push(t => {...})` registra a animação por quadro. Dentro de um update é permitido somar
  `s.el.style.transform += ...` (tremor) e alterar `s.el.style.filter/opacity` (fade de saída).
- `bg(s, src, {z0, z1, px, py, filter, origin})`: foto em tela cheia com Ken Burns (zoom de `z0` para `z1` e deslocamento).
- `shade(s, css)`: camada por cima, para gradientes, multiply colorido etc.
- `el(tag, classe, pai, html)`: cria um elemento. Use a classe `'abs'` para posicionamento absoluto.
- `.ht`: retícula de halftone (multiply).

## Texto cinético
- `seq(s, x, y, i0, i1, opts, porPalavra)`: linha com as palavras `i0..i1` da narração, cada uma entrando no tempo
  em que é falada (blur → nítido, escala 1,2 → 1, cor apagada → final), e a linha se recentralizando suavemente.
  - `opts`: `font` (ver FONTS), `color`, `from` (cor inicial), `glow` (rgba), `align` ('center' | 'left' | 'right'),
    `outAt` (instante em que a linha some com blur), `text: {i: 'texto'}` (substitui a palavra exibida),
    `lead` (antecipação em s, padrão 0,04).
  - `porPalavra[i]`: os mesmos campos, por palavra (ex.: destacar a palavra-chave).
  - A pontuação final (.,:) é removida automaticamente; `?` fica.
- `line(s, x, y, [[texto, t0, opts], ...], opts)`: o mesmo, com textos e tempos livres.
- `rec.extra = t => 'rotate(-3deg)'`: transformação extra numa linha retornada por `seq`/`line`.
- `typer(pai, css, texto, t0, cps)`: efeito de máquina de escrever. Chame `.at(t)` no update.
- `FONTS.sans(px, peso)` (Inter), `FONTS.serif(px)` (Playfair 900 itálico), `FONTS.caps(px)` (Anton),
  `FONTS.type(px)` (Special Elite), `FONTS.hand(px)` (Caveat), `FONTS.dms(px, italico)` (DM Serif Display).

## Recursos prontos
- Emojis: `tw('1f621')` devolve o caminho do SVG do Twemoji (código unicode em hexa).
- Filtros SVG: `filter:url(#rough)` (borda tremida de carimbo ou traço à mão), `url(#paperF)` (textura de papel:
  `<svg><rect width="100%" height="100%" filter="url(#paperF)"/></svg>`).
- Traço desenhado: um path SVG com `stroke-dasharray = L` e `stroke-dashoffset = L*(1-p)`.

## Finalização
`finalize({ duration, grain=0.08, vignette=0.4, flashes: [[t, dur, 'r,g,b'?], ...], preload: [] })`.
Os flashes servem para cortes de cena (branco por padrão; `'227,20,27'` dá vermelho).

## Verificação de layout
- `node render.js video.html --check` roda `window.layoutCheck()` e lista CORTE, SOBREPOSIÇÃO, APERTADO e ELEMENTO.
  Sai com código 2 se houver problema.
- Marque fotos, cartões e carimbos que não podem cobrir texto com o atributo `data-evitar="descrição"`.
- Regras de diagramação: margem lateral de 40 px; linhas de 2 a 4 palavras; espaço entre centros de linhas
  de 1,1 a 1,3 × a maior fonte das duas (nem apertado, nem espaçado; blocos separados de propósito usam `{ livre: true }`); a palavra-chave gigante (≥ 90 px) fica sozinha na linha.

## Armadilhas já resolvidas (não repita)
- Texto passando da largura da tela: quebre em mais `seq()`. Confira **sempre** nas prévias.
- Elementos absolutos com texto (carimbos, etiquetas) quebram linha sozinhos: use `white-space:nowrap`.
- Voz com atraso em relação aos tempos: a voz sempre começa em t=0 no `mixar.py`, e os tempos vêm do `tighten.py`.
- Animações em segundos fixos quebram quando a narração muda: use `ws()`/`we()` e derive `DUR` do fim da última palavra.
