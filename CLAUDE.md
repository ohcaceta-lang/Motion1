# Motion1 — regras para criar vídeos

Este repositório guarda vídeos virais verticais (Reels/TikTok/Shorts) e as referências de animação do usuário.

## Regras obrigatórias em TODO vídeo
1. **Sempre usar as referências de `referencias/`.** Antes de animar, leia
   `skills/videos-virais-reels/references/referencias-pinterest.md` (resumo e DNA) e, para cada versão,
   o `analise.md` + `contact-sheet.jpg` da referência escolhida. Use as técnicas (tipografia, transições,
   tratamento de imagem, ritmo), nunca o conteúdo. Se houver referências novas na pasta, leia-as também.
2. **Sempre entregar versões diferentes**: no mínimo **2 versões** do mesmo vídeo, cada uma baseada em uma
   referência diferente (paleta, fontes, transições e assinaturas visuais distintas). A narração, a música e
   as imagens podem ser reaproveitadas entre versões (sem custo extra no Pikaso). Nomeie como
   `Titulo_V1_<estilo>.mp4`, `Titulo_V2_<estilo>.mp4`.
3. **Sempre animação de verdade**: câmera sempre em movimento, transições motivadas, pelo menos um destaque
   animado por cena (caixa, grifo, cursor, objeto entrando, contador, traço desenhado). Siga o checklist de
   capricho do `referencias-pinterest.md` e rode `node render.js video.html --check` (LAYOUT OK) em cada versão.
4. **Sempre gerar a descrição com SEO para o TikTok** em `descricao_tiktok.txt` na pasta do vídeo:
   - primeira linha com o gancho e as palavras-chave principais (nome, assunto);
   - 2 a 3 frases com os fatos e palavras-chave naturais;
   - CTA para comentar;
   - 8 a 12 hashtags (mistura de nicho + amplas, ex.: #fyp);
   - título sugerido para a capa, lista de palavras-chave de busca, dicas de postagem, fontes e crédito das fotos.
5. Assuntos públicos: fotos reais das pessoas envolvidas com crédito visível na tela; nunca gerar rostos reais com IA.
6. Narração: Camila Rocha aprovada; Caio Nogueira reprovada. Pikaso sempre no menor custo.

## Estrutura de cada vídeo
`videos/<slug>/` com: os MP4 finais de cada versão, `video_v1.html`, `video_v2.html`…, `cues.json`, `assets/`
(imagens, `words.js`, `voz_edit.json`), scripts de render e `descricao_tiktok.txt`.

## Git
Trabalhe na branch indicada pela sessão, faça commit e push ao terminar cada vídeo.
