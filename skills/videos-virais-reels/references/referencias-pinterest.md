# Referências de animação do usuário (Pinterest)

O usuário salvou vídeos de referência no repositório **Motion1**, pasta `referencias/`. Cada subpasta tem
`video.mp4`, `frames/` (2 por segundo), `contact-sheet.jpg` e `analise.md` (decupagem cena por cena).
**Este é o padrão de qualidade.** Antes de animar, leia este resumo e, se o vídeo pedir um estilo parecido, abra
o `contact-sheet.jpg` e o `analise.md` da referência mais próxima. Use as técnicas, nunca copie o conteúdo.

Novas referências podem ser adicionadas a qualquer momento: liste a pasta e leia os `analise.md` novos.

## As referências e quando usar cada uma

| Pasta (em `referencias/`) | Estilo | Use para |
|---|---|---|
| `insta-trend-documentary-motion-…` | Revista/editorial, abre claro e vira azul-marinho, post 3D, glassmorphism, final "I'M ARTIST" com grão | Manifesto, motivação, criadores |
| `motion-design-earnedits-…` | Vinho com vinheta, palavra-chave serifada gigante + objeto 3D cromado, eco de texto, 16 fps | Polêmica, opinião, "a verdade sobre" |
| `branding-why-storytelling-earnedits-…` | Uma cena-mundo por frase (HUD técnico, notificação de celular, lousa a giz, jornal), objeto-herói constante | Lições de marca/negócios |
| `agencia-marketing-exar-…` | P&B minimalista, círculo tracejado se desenhando, lista numerada 1-2-3, whip com motion blur | Anúncio curto (≤15 s), dicas em lista |
| `vender-sem-palavras-insiderforce-…` | Cinza monocromático, canvas infinito com câmera contínua, caixas e conectores tracejados, objetos 3D P&B | Explicar conceitos (psicologia, ciência) |
| `marca-forte-cynosure-…` | Gradiente mesh vermelho animado ↔ branco, cursor clicando para destacar, pílulas caindo na lixeira, números com onda | Institucional/portfólio, resultados |
| `corretora-confiavel-pfh-…` | P&B + acento amarelo, tarja nos olhos, "Not another…", pilares "Highly X" com objetos 3D | Anúncio de serviço, confiança |
| `posicionamento-al-ries-rivinity-…` | Bege-papel (história) → azul-noite neon (aplicação), livro 3D grifado, linha contínua sem cortes | Aula/conceito com autor e exemplos |
| `mcdonalds-imoveis-earnedits-…` | Personagem fixo de IA mudando de cenário a cada passo, traços à mão amarelo-limão, pausas em papel | **Curiosidades de empresas** (canal dark) |

## Técnicas que se repetem (o "DNA" do que o usuário gosta)

### Texto
- **Contraste de hierarquia na mesma frase:** palavra de ligação pequena (regular ou itálica) + palavra-chave grande
  (bold/serifada), 1,8–2,5× maior. Frases em **blocos compactos** (centros de linha a 1,1–1,3× a fonte), nunca espalhadas.
- **Destaque ativo da palavra:** caixa sólida surgindo atrás (branca/vermelha), **cursor de mouse clicando** na palavra,
  **grifo de marca-texto** passando, sublinhado desenhado, círculo à mão em volta de números.
- **Eco/repetição:** a mesma palavra empilhada 3–4 vezes com opacidade decrescente para dar ênfase.
- **Palavra gigante final** ("ARTIST", "MOVE") recortada pela borda ou com letras vazadas.
- **Microtipografia editorial** nas bordas (data, código de barras, texto vertical, número de página) para o acabamento "premium".

### Imagens e recortes
- **Objetos recortados** (PNG sem fundo) entrando com overshoot, girando levemente, com sombra suave; caindo em cena
  (dinheiro, tênis, ícones 3D, ferramentas). Use `images_remove_background`.
- **Um tratamento único para todas as imagens** (tudo P&B, ou tudo duotone, ou tudo cromado) para unificar fontes diferentes.
- **Camadas de profundidade:** primeiro plano desfocado (folhas, setas, pessoa passando), assunto nítido e fundo com luz/círculos.
- **Mockups do cotidiano:** notificação de celular, post do Instagram em 3D, comentários em vidro fosco, barra de busca digitando, visor de câmera REC.
- **Personagem fixo** (gerado por IA, fictício) mudando de pose e cenário para contar um processo passo a passo.
- **Metáfora visual forte** para fechar o argumento (marionete, lixeira, olho, troféu).

### Movimento e transições
- **A câmera nunca para:** zoom/pan lento contínuo; em explicativos, **canvas infinito** em que a câmera desliza de um conceito ao outro.
- **Transições motivadas, não cortes secos:** whip com motion blur, zoom para dentro de um objeto (notificação → próxima cena),
  linha contínua que vira círculo/onda/trilho, onda branca subindo do rodapé, círculo que engole a tela, zoom blur radial.
- **Um único corte seco** (ou poucos) para marcar a virada da história (problema → solução, pergunta → resposta).
- **Elementos que se desenham:** círculo tracejado, conectores, setas, check-boxes aparecendo uma a uma.
- **Fundo vivo:** gradiente mesh animado, grão de filme, partículas/poeira, luz pulsando.

### Ritmo e estrutura
- Uma ideia nova a cada **1,5–3 s**; o momento de "ensinar" (lousa, frase central) pode durar 4–5 s.
- Estruturas que funcionaram: **mito → verdade → como funciona em 3 passos → número → virada → CTA**;
  **pergunta polêmica → "todo mundo diz…" → 3 argumentos → virada → CTA**; **lista de 3 erros numerados → solução → slogan**.
- **CTA com isca:** "comente PALAVRA e receba X" + mockup de comentário/checklist/botão "link na bio" com cursor clicando.

## Checklist de capricho antes do render
- [ ] Cada cena tem movimento de câmera **e** pelo menos uma animação de destaque (caixa, cursor, grifo, objeto entrando).
- [ ] Transições motivadas; cortes secos só onde a história vira.
- [ ] Objetos e pessoas que ficam "soltos" na cena estão recortados, com sombra.
- [ ] Textos em blocos compactos, bem alinhados, sem buracos (`--check` com LAYOUT OK, sem `ESPAÇADO`).
- [ ] Paleta e tratamento de imagem consistentes do começo ao fim.
- [ ] Final com palavra/visual forte e CTA claro.
