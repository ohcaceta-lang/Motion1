# Motion1 — regras para criar vídeos (REGRA FIXA DO USUÁRIO)

Este repositório guarda vídeos virais verticais (Reels/TikTok/Shorts) e as referências de animação do usuário.

## ✅ Checklist obrigatório antes de entregar QUALQUER vídeo novo
- [ ] Animação baseada numa referência de `referencias/` diferente das já usadas (ver Histórico), com novidade.
- [ ] Texto de cada cena num **único bloco compacto e centralizado** (`bloco()`), sem linhas espalhadas nem buracos.
- [ ] `node render.js video.html --check` → **LAYOUT OK** (sem CORTE, APERTADO, ESPAÇADO, SOBREPOSIÇÃO, ELEMENTO).
- [ ] Prévia (folha de frames) conferida a olho: blocos alinhados, nada solto no rodapé, palavra-chave em destaque.
- [ ] `descricao_tiktok.txt` com SEO salvo e colado no fim da resposta.
- [ ] Histórico de estilos atualizado, commit e push.

## Regras obrigatórias em TODO vídeo
1. **Um vídeo por pedido.** Não gerar várias versões do mesmo vídeo, a não ser que o usuário peça.
2. **Animação sempre diferente e com novidade, conforme as referências.** A cada nova conversa/vídeo:
   - leia `skills/videos-virais-reels/references/referencias-pinterest.md` e o `analise.md` + `contact-sheet.jpg`
     da referência escolhida em `referencias/` (se houver referências novas na pasta, leia-as também);
   - consulte o **Histórico de estilos** abaixo e escolha uma referência/combinação **que ainda não foi usada**
     (ou a menos recente), trazendo pelo menos uma técnica de animação nova em relação aos vídeos anteriores
     (transição, tratamento de imagem, tipografia, assinatura visual);
   - use as técnicas, nunca o conteúdo da referência;
   - câmera sempre em movimento, transições motivadas, um destaque animado por cena, e
     `node render.js video.html --check` com LAYOUT OK.
3. **Texto organizado, compacto e sem buracos (o usuário reclamou de texto espaçado e legendas "jogadas").**
   - Use os scripts **deste repositório** (`skills/videos-virais-reels/scripts/lib.js` e `render.js`), que têm a
     função `bloco()` e a conferência `ESPAÇADO`; copie-os para a pasta do projeto por cima dos do `setup.sh`.
   - Todo o texto de uma cena entra com **`bloco(s, yCentro, linhas)`**: as linhas são empilhadas automaticamente
     com centros a ~1,25 × a fonte, formando **um único bloco centralizado**. Nunca posicione linhas soltas com `y` fixo
     espalhado pela tela. Contadores e cartões que ficam entre linhas entram no bloco com `{ el, h }`.
   - Um bloco por cena, sempre na mesma faixa da tela (centro ~600–660 px; abaixo da foto quando houver foto no topo).
     Fotos, placares e cartões ficam logo acima ou abaixo do bloco, colados nele, nunca isolados no rodapé.
   - No máximo 4 a 5 linhas visíveis ao mesmo tempo, de 2 a 4 palavras cada, e no máximo 1 palavra-chave grande por linha.
   - `node render.js video.html --check` precisa dar LAYOUT OK **sem `ESPAÇADO`** e sem `APERTADO`.
4. **Sempre terminar com a descrição para o TikTok** (com SEO), salva em `descricao_tiktok.txt` na pasta do vídeo
   e também colada na resposta final ao usuário:
   - primeira linha com o gancho e as palavras-chave principais (nome, assunto);
   - 2 a 3 frases com os fatos e palavras-chave naturais;
   - CTA para comentar;
   - 8 a 12 hashtags (nicho + amplas, ex.: #fyp);
   - título sugerido para a capa, palavras-chave de busca, dicas de postagem, fontes e crédito das fotos.
5. Ao terminar, **acrescente o vídeo ao Histórico de estilos** deste arquivo (data, pasta, referência e técnicas novas).
6. Assuntos públicos: fotos reais das pessoas envolvidas com crédito visível na tela; nunca gerar rostos reais com IA.
7. Narração: Camila Rocha aprovada; Caio Nogueira reprovada. Pikaso sempre no menor custo.

## Estrutura de cada vídeo
`videos/<slug>/` com: o MP4 final, `video.html`, `cues.json`, `assets/` (imagens, `words.js`, `voz_edit.json`),
scripts de render e `descricao_tiktok.txt`. Commit e push na branch indicada pela sessão ao terminar.

## Histórico de estilos (não repetir o mais recente; priorize referências ainda não usadas)
| Data | Vídeo (pasta) | Referência / estilo | Técnicas usadas |
|---|---|---|---|
| — | `videos/escala6x1` | (anterior às regras) | — |
| — | `videos/polemica-projeto` | (anterior às regras) | — |
| — | `videos/tech-em-alta` | (anterior às regras) | — |
| 14/11/2026 | `videos/alan-ruschel-despedida` (V1) | Cinemático próprio (preto, verde, ouro) | polaroid caindo, rota do voo tracejada, contadores, carimbo, comentário digitando |
| 14/11/2026 | `videos/alan-ruschel-despedida` (V2) | `insta-trend-documentary-motion` | abertura clara → azul-marinho, cursor + caixa tracejada, cards 3D, pílulas com slide, infográfico de pontos, corte seco com grão, microtipografia de revista |
| 14/11/2026 | `videos/alan-ruschel-despedida` (V3) | `motion-design-earnedits` | vinho + vinheta, palavras gigantes cortadas, eco de texto, stickers P&B caindo, 16 fps, rodapé de post |
| 17/11/2026 | `videos/apagao-mundial` | `vender-sem-palavras-insiderforce` | cinza com grade + acento vermelho, **canvas infinito** (4 estações tracejadas ligadas por "?", câmera zoom-out/pan contínuo com motion blur), apagão por **inversão da cena** piscando, objetos P&B em multiply com máscara radial, rótulo tracejado se desenhando, risco vermelho na palavra, 5 "ilhas" de rede, mockup de post com contador de views, cursor clicando |

Referências ainda **não usadas**: `branding-why-storytelling-earnedits`, `agencia-marketing-exar`,
`marca-forte-cynosure`, `corretora-confiavel-pfh`,
`posicionamento-al-ries-rivinity`, `mcdonalds-imoveis-earnedits`.
