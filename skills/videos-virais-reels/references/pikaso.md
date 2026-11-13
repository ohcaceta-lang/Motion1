# Pikaso (Magnific) MCP: narração, música e imagens

Ferramentas: `mcp__Pikaso__*`. Carregue com ToolSearch, por exemplo:
`select:mcp__Pikaso__audio_tts,mcp__Pikaso__audio_timing_get,mcp__Pikaso__audio_music_generate,mcp__Pikaso__images_generate,mcp__Pikaso__creations_wait,mcp__Pikaso__simulate_cost,mcp__Pikaso__account_balance,mcp__Pikaso__audio_voices_list`

## Regra de custo do usuário
**Sempre o mais barato.** Pelo MCP, o modo ilimitado da conta **não vale**: `account_balance` mostra
`unlimitedAppliesHere: false` e `simulate_cost` mostra `isUnlimited: false` para todos os modelos.
Se um dia aparecer `isUnlimited: true` em algum modelo, use esse. Confira com `simulate_cost` antes de
gerar algo novo e informe o custo total no final.

| Item | Escolha | Custo de referência |
|---|---|---|
| Narração | `audio_tts`, `model: eleven_turbo_v2_5` (o `eleven_v4` custa o dobro) | ~45–80 créditos por narração de 30–45 s |
| Música | **banco de músicas** (pasta `musicas/` ou `stock_search`, ver abaixo); gerar com `google-lyria-3` só em último caso | 0 no banco; 80 se gerar |
| Imagens | `images_generate`, `mode: fast` (Classic Fast), `aspectRatio: 9:16` | 1 por imagem |
| Efeitos sonoros | **não use o Pikaso**: gere grátis com `synth.py`/`mixar.py` | 0 |

Total típico por vídeo: 60–100 créditos com música do banco (140–180 se a música for gerada), mais os recortes.

## Narração (TTS)
- `eleven_turbo_v2_5` só entende pausas `(pause 500ms)`; qualquer outro colchete é **lido em voz alta**.
  Pausas explícitas deixaram a fala lenta (52 s para um roteiro de 30 s). Prefira **não pôr pausas**:
  use pontuação (vírgula, reticências, ponto), `speed: 1.08`, `stability: 0.4`, `similarityBoost: 0.8`.
- Escreva números por extenso ("setenta e dois metros quadrados", "dois mil e dois").
- Vozes (pt-BR) já testadas:
  - **Camila Rocha (id 449)**: feminina, doce, envolvente. Aprovada para lifestyle.
  - **Joana Cordeiro (id 1069)**: feminina, calma, indicada para true crime e mistério, mas **lenta** (110 palavras deram 68 s). Use roteiro de até 75 palavras ou prefira a Camila.
  - Caio Nogueira (id 949): **reprovada** pelo usuário ("muito feia"). Não use.
  - Outras promissoras: Tiago Macedo (1409, locutor), Duarte Queiroz (1060, documentário),
    Henrique Teixeira (1240, natureza), Mariana Sampaio (939, suave).
  - Para mais opções, use `audio_voices_list` com `search: "portuguese"`.
- Depois de `creations_wait`, chame `audio_timing_get` com `limit: 100` (e `offset` se `hasMore`).
  Ele devolve o início e o fim de cada palavra. **Ignore as entradas "."**.

## Música (do banco, não gerada: preferência do usuário)
O usuário quer **músicas do banco de músicas do Pikaso/Freepik**, e não geradas por IA. Ordem:
1. **Pasta `musicas/` do repositório Motion1:** faixas que o usuário baixou do banco de músicas do Pikaso/Freepik.
   Escolha pelo clima (o nome do arquivo e o `musicas/LEIA-ME.md` descrevem cada uma). Confira duração e volume com
   `ffprobe`/`volumedetect`; o `mixar.py` faz o loop e o ducking.
2. **Banco via MCP:** teste se `stock_search` passou a aceitar áudio (`content_type: "music"` ou `"audio"`). Em nov/2026
   ele **não** aceitava (só photo, vector, illustration, psd, design, video, icon, 3d). Se passar a aceitar, busque
   pelo clima, baixe com `stock_download` e prefira faixas `license: free`.
3. **Só em último caso** (nenhuma faixa adequada nos passos 1 e 2): gere com `audio_music_generate`
   (`google-lyria-3`, 80 créditos) e **avise o usuário na entrega** que a música foi gerada e qual faixa do banco
   seria bom ele baixar para a pasta `musicas/`.
- Prompt de geração (só no passo 3) em inglês, com gênero, clima, instrumentos, BPM e "instrumental, no vocals". Exemplos:
  - true crime: `Dark cinematic true crime documentary underscore, slow 70 BPM, deep sub drone, muted heartbeat pulse, sparse melancholic piano in D minor, tense low strings, instrumental, no vocals`
  - lifestyle: `Warm acoustic folk instrumental, fingerpicked acoustic guitar, soft shaker, gentle piano, 95 BPM, peaceful countryside morning, hopeful and cozy, instrumental, no vocals`
  - tech/negócios: `Modern minimal electronic pulse, 110 BPM, deep bass, glitchy percussion, tense synth arpeggio, corporate thriller, instrumental, no vocals`

## Recortes (remoção de fundo)
- `images_remove_background` com o `creationIdentifier` da imagem: devolve PNG transparente (ou sobre uma cor com `backgroundColor`).
- Imagem que não veio do Pikaso (foto real, frame): envie antes com `creations_upload_image` e use o id retornado.
- Confira o custo com `simulate_cost` na primeira vez do vídeo e some ao total.
- Gere objetos já pensando no recorte: "isolated on plain white background, studio lighting, soft shadow, no text".
- Depois do recorte: confira as bordas (Read numa miniatura), aplique `filter: drop-shadow(...)` e, para parallax,
  separe em camadas (fundo, assunto recortado e primeiro plano desfocado).

## Imagens
- No Pikaso, gere só **cenários, objetos e ambientes** (relógio, dossiê, sala vazia, montanhas, cabana, chips, prédio).
  **Pessoas reais entram com fotos reais** (`buscar_fotos.py`: Wikimedia Commons ou foto da matéria, com crédito);
  nunca gere nem edite com IA o rosto de uma pessoa real, porque uma cena fabricada engana o público.
  Pessoas fictícias ou anônimas podem ser silhuetas ou cartões com "?".
- Escreva "no people" e "no readable text" quando fizer sentido.
- Gere todas as imagens do vídeo em chamadas paralelas e depois um `creations_wait` com até 8 ids por vez.

## Download dos arquivos
Os resultados ficam em `https://pikaso.cdnpk.net/...` (a `url` de `creations_wait`). O host
`pikaso.cdnpk.net` precisa estar liberado na rede do ambiente. Baixe com `curl -sS -m 90 -o arquivo "URL"`,
com até 3 tentativas.
