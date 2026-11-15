---
name: "videos-virais-reels"
description: "Vídeos Virais-Reels: cria vídeos verticais (9:16) prontos para postar no Instagram Reels, TikTok e Shorts, com narração em português (ElevenLabs via Pikaso), música de fundo, efeitos sonoros, tipografia animada palavra por palavra e cenas no estilo de editores de motion design. Pesquisa o que está em alta (Google Trends, Google News, G1), checa os fatos, escreve o roteiro, gera voz, música e imagens no Pikaso pelo menor custo, anima, renderiza e entrega o MP4 final. Use sempre que o usuário pedir um vídeo, reel, short, TikTok ou conteúdo para redes sobre um assunto, notícia, polêmica, famoso, empresa ou tema em alta, ou pedir para recriar, analisar ou decupar um vídeo de referência, mesmo que não diga 'skill' nem 'Reels'."
---

# Vídeos Virais-Reels

Produz vídeos curtos e verticais de nível profissional **de ponta a ponta, sem o usuário precisar editar nada**.
O usuário prefere receber a **entrega finalizada**: não pare para pedir aprovação de roteiro ou estilo, a
menos que o pedido seja ambíguo. Decida, produza, confira e entregue.

**Sempre capriche.** O padrão de qualidade são as referências do Pinterest que o usuário salvou
(`references/referencias-pinterest.md` e a pasta `referencias/` do repositório Motion1). Um vídeo "ok" não basta:
cada cena precisa de animação bonita, texto bem espaçado, recortes limpos, narração sem erro e som caprichado.

## Recursos da skill
- `scripts/setup.sh`: prepara a pasta do projeto (copia scripts e instala fontes, emojis e scipy).
- `scripts/buscar_em_alta.py`: trends, notícias e leitura de matérias do G1.
- `scripts/buscar_fotos.py`: fotos **reais** de figuras públicas (Wikimedia Commons e fotos das matérias do G1, com legenda e crédito).
- `scripts/tighten.py`: encurta pausas longas da narração e gera os tempos de cada palavra.
- `scripts/lib.js` + `assets/template.html`: motor de animação e modelo de vídeo.
- `scripts/render.js`: prévias em PNG e render final (Chromium/Playwright + ffmpeg).
- `scripts/mixar.py` + `scripts/synth.py`: mixagem (voz, música em loop com ducking, efeitos sintetizados) e MP4 final em -14 LUFS.
- `references/estilos.md`: **leia antes de criar as cenas**. São 6 estilos, com paleta, fontes, cenas e sons.
- `references/pikaso.md`: **leia antes de gerar qualquer coisa no Pikaso**. Tem custos, vozes aprovadas e reprovadas e o download.
- `references/lib-api.md`: API do motor de animação e armadilhas já resolvidas.
- `references/roteiro-e-fatos.md`: estrutura de roteiro e checagem de fatos. Leia quando o tema envolver pessoas reais.
- `references/referencias-pinterest.md`: **leia antes de animar**. Técnicas de animação tiradas das referências que o usuário escolheu.
- `references/google-flow.md`: Google Flow (imagens e clipes de B-roll) rodando no PC do usuário via lote JSON; ajuste de idioma em `scripts/flow/`.

## Pré-requisitos do ambiente
- Rede: `trends.google.com`, `news.google.com`, `g1.globo.com` (pesquisa), `pikaso.cdnpk.net` (download do Pikaso) e
  `commons.wikimedia.org`, `upload.wikimedia.org`, `s2-g1.glbimg.com` (fotos reais).
  Se um desses estiver bloqueado, proponha a liberação ao usuário com a ferramenta de ambiente disponível
  (em sessões na nuvem: `update_environment`), dizendo em uma frase o motivo.
- MCP do Pikaso conectado (ferramentas `mcp__Pikaso__*`).
- Node com Playwright/Chromium, ffmpeg e Python 3 com numpy. O `setup.sh` instala o scipy.

## Fluxo

### 1. Projeto
```bash
bash <skill>/scripts/setup.sh /home/user/videos/<tema-curto>
```
Trabalhe dentro dessa pasta. Os arquivos gerados vão para `assets/`.

### 2. Pauta e fatos
- Sem tema dado: `python3 buscar_em_alta.py trends BR` e escolha o de maior volume com boa cobertura.
- Sempre: confirme os fatos em 2 ou mais fontes (`news`, `g1`, `ler`). Siga `references/roteiro-e-fatos.md`:
  com pessoas reais, alegação é "suposta" ou "segundo o jornal".
- **Assunto público = fotos reais das figuras públicas envolvidas (preferência do usuário).** Veja a seção abaixo.

### 3. Roteiro (padrão 30–45 s, 80–110 palavras; pode ser mais longo quando o tema pedir)
Gancho → contexto → 2 ou 3 fatos concretos → virada → CTA em pergunta. Frases curtas e números por extenso.

**Vídeos mais longos e explicativos são permitidos quando necessário** (decisão sua, sem perguntar ao usuário):
quando o tema tem passo a passo, história com várias etapas, conceito que precisa de exemplos ou muitos fatos
que não cabem em 45 s sem ficar raso ou corrido. Nesses casos:
- **Formato explicativo: 60–90 s (160–230 palavras)**; até ~3 min (cerca de 450 palavras) se o conteúdo realmente exigir.
  Não estique: se dá para contar bem em 45 s, faça 45 s.
- Estrutura em **capítulos**: gancho forte (0–3 s) → promessa ("vou te mostrar 3 motivos…") → blocos de 15–25 s,
  cada um com mini-título/número na tela → recapitulação curta → CTA. Uma ideia por cena, como sempre.
- **Retenção:** um "gancho de continuidade" a cada 15–20 s ("mas o mais curioso vem agora…"), troca de cenário ou
  de estilo de cena a cada capítulo e barra de progresso discreta ou numeração de capítulos.
- Use os formatos explicativos das referências (canvas infinito com câmera contínua, lousa, livro grifado,
  personagem fixo passo a passo; ver `references/referencias-pinterest.md`).
- Técnico: `audio_timing_get` exige paginação (`offset`) acima de 100 palavras; a música do banco entra em loop
  com crossfade pelo `mixar.py`; com muitas cenas, gere as imagens em lotes de até 8 e faça a prévia (passo 8)
  por capítulo. O custo sobe com a narração e as imagens: confira com `simulate_cost` e informe no final.
- Avise na entrega por que o vídeo ficou mais longo, e sugira uma versão curta (corte de 30–45 s) para Reels se fizer sentido.
Escolha o estilo em `references/estilos.md` e a voz em `references/pikaso.md`.

### 4. Pikaso (sempre o menor custo)
Em paralelo, na mesma rodada:
- `audio_tts`: `eleven_turbo_v2_5`, voz escolhida, `speed 1.08`, `stability 0.4`, `similarityBoost 0.8`, **sem marcações de pausa**.
- **Música: do banco de músicas, não gerada** (preferência do usuário). Veja "Música" em `references/pikaso.md`.
- `images_generate`: `mode: fast`, `9:16`, de 4 a 7 **cenários e objetos** (ambiente, clima, metáforas visuais). Pessoas reais vêm de fotos reais, nunca do Pikaso.
- **Recortes:** sempre que um objeto, produto ou pessoa precisar aparecer solto na cena (colagem, sticker 3D, pessoa
  saindo da foto, objeto caindo, parallax em camadas), **faça o recorte**: `images_remove_background` no Pikaso
  (PNG transparente). Para fotos reais baixadas fora do Pikaso, envie antes com `creations_upload_image`. Gere os objetos
  já pensando no recorte ("isolated on plain white background, studio lighting"). Confira o PNG (Read) e, se a borda
  ficou suja, refaça; dê sombra suave (`drop-shadow`) para o recorte não parecer colado.

Alternativa para cenários e clipes de B-roll: **Google Flow** no PC do usuário (veja `references/google-flow.md`).
Escreva o `lote.json`, o usuário roda e faz commit dos arquivos em `assets/`.

Depois, `creations_wait`, download com curl para `assets/` e `audio_timing_get` (limit 100, pagine se precisar).

### 4b. Revisão da narração (obrigatória: erros de narração não podem passar)
Antes de animar, confira se a voz falou exatamente o roteiro e pronunciou tudo certo:
1. **Revisão do texto antes do TTS:** números, datas, siglas, valores e palavras estrangeiras escritos como devem ser
   falados ("dois mil e vinte e quatro", "éfe-bê-í", "Mêc Donalds"), sem abreviações, sem parênteses nem símbolos (%, $, &).
2. **Transcrição da voz gerada:** ponha a narração num vídeo simples (ex.: `ffmpeg -f lavfi -i color=black:s=360x640 -i voz.mp3 -shortest voz_check.mp4`),
   envie com `creations_upload_file` e use `video_analyze` (gratuito) perguntando:
   "Transcreva a narração em português palavra por palavra e aponte palavras mal pronunciadas, sotaque estrangeiro,
   sílabas engolidas, ênfase errada, palavras repetidas ou faltando."
3. **Compare com o roteiro** e confira também os tempos do `audio_timing_get`: palavra com duração estranha
   (muito longa ou curtíssima para o tamanho) costuma ser erro de pronúncia.
4. **Corrija:** reescreva só o trecho com problema (grafia fonética, vírgula para a entonação, trocar a palavra por
   sinônimo) e gere de novo. Repita até a narração sair limpa. Registre no final o que foi corrigido.

### 5. Tempos das palavras
Grave os tempos em `assets/words.txt` no formato `palavra inicio fim|palavra inicio fim|...`
(pulando as entradas ".") e rode:
```bash
python3 tighten.py assets/voz.mp3 assets/words.txt assets/voz_edit 1.0
echo "window.WORDS = $(cat assets/voz_edit.json);" > assets/words.js
```
O tempo 1.0 mantém a velocidade e só encurta pausas exageradas. Use 1.1 se a fala ficou arrastada (mais de 50 s).
Liste os índices para planejar as cenas:
`python3 -c "import json;[print(i,d['w'],d['s']) for i,d in enumerate(json.load(open('assets/voz_edit.json')))]"`

### 6. Animação
Edite `video.html` a partir do template, seguindo o estilo escolhido e `references/lib-api.md`:
- uma cena por frase ou fato, com corte em `ws(i)` da primeira palavra, e `DUR` = fim da última palavra + 2 s;
- palavra-chave destacada em cada linha; imagem com Ken Burns e escurecida para leitura;
- pelo menos uma "assinatura" visual por cena (contador, carimbo, alfinete, fio vermelho, mapa, polaroid, enquete);
- **animações no nível das referências** (`references/referencias-pinterest.md`): câmera sempre em movimento,
  transições motivadas (whip com motion blur, zoom para dentro de um objeto, linha contínua, onda subindo),
  objetos recortados entrando com overshoot e sombra, palavra destacada com caixa/cursor/marca-texto,
  camadas de profundidade (primeiro plano desfocado). Nada de texto parado em fundo parado;
- CTA final com enquete ou caixa de comentário.

### 7. Quebra de texto e espaçamento (o usuário considera isso MUITO importante)
Texto cortado na borda ou linhas grudadas são o erro que o usuário mais percebe. Por isso a conferência é
**automática e obrigatória** antes de qualquer render final:
```bash
node render.js video.html --check
```
Ele mede cada linha depois que ela termina de aparecer e acusa:
- `CORTE`: a linha sai da margem segura de 40 px de cada lado;
- `SOBREPOSIÇÃO`: duas linhas se cruzam;
- `APERTADO`: o espaço entre linhas vizinhas é menor que 22% da altura;
- `ESPAÇADO`: o espaço entre linhas vizinhas do mesmo bloco é maior que 65% da altura (**o erro que mais
  apareceu nos últimos vídeos: texto solto, com buracos entre as linhas**);
- `ELEMENTO`: o texto cruza foto, carimbo ou cartão marcado com `data-evitar`.

**Só renderize com `LAYOUT OK`.** Como corrigir:
- frase longa: quebre em mais `seq()` de 2 a 3 palavras (ex.: "foram condenados" / "pelo crime"), em vez de só diminuir a fonte;
- linhas apertadas: aumente o `y` da linha de baixo;
- linhas espaçadas demais: diminua a distância. **Regra de ouro: entre centros de linhas do mesmo bloco, de 1,1 a 1,3 ×
  a maior fonte das duas** (ex.: 50 px e 96 px → centros a 106–125 px). A frase deve parecer **um bloco só**, como nas
  referências ("Growth needs / strategy + creativity"); não espalhe as linhas pela tela;
- elementos que são de propósito separados do bloco (rótulo no topo, crédito, CTA no rodapé) recebem `{ livre: true }`
  no `seq()`/`line()`. Use com moderação: se a dúvida for "está longe demais?", provavelmente está;
- palavra-chave grande dentro de linha comprida: deixe a palavra-chave sozinha numa linha;
- carimbo ou foto em cima do texto: mova o elemento ou o texto e marque fotos e cartões com `data-evitar="foto"`.

### 8. Prévia e conferência visual (não pule)
```bash
node render.js video.html /tmp/prev --preview 1.0,4.5,9.0,...   # um instante por cena, perto do fim de cada uma
ffmpeg -pattern_type glob -i '/tmp/prev_*.png' -vf "scale=200:-1,tile=6x2" /tmp/folha.png
```
Olhe a folha (Read). Confira **com atenção o espaçamento entre os textos** (blocos compactos, sem buracos, margens
equilibradas) e o que o `--check` não mede: elementos invisíveis, cores erradas, foto cobrindo rosto,
hierarquia (a palavra-chave se destaca?) e respiro geral. Repita `--check` e a prévia até ficar limpo.

### 9. Som
Monte `cues.json` com os efeitos amarrados aos mesmos instantes das animações (whoosh nos cortes, impacto nas
revelações, carimbo no carimbo, `ticks` nos contadores, `typing` na datilografia, ambiente do tema).
Veja a lista em `scripts/mixar.py`. Use `ws()` calculado em Python para os tempos:
```bash
node render.js video.html mudo.mp4
python3 mixar.py --voz assets/voz_edit.wav --musica assets/musica.mp3 --dur <DUR> --cues cues.json \
  --out mix.wav --video mudo.mp4 --final <Titulo_do_Video>.mp4
```

### 10. Entrega
- Extraia de 8 a 10 frames do MP4 final em uma folha e confira (inclui sincronia: a palavra aparece quando é falada).
- Envie o MP4 com a ferramenta de envio de arquivos (ex.: SendUserFile, `display: render`).
- Resposta curta: tema e por que está em alta, o que tem no vídeo (estilo, voz e som), as fontes checadas,
  o **custo em créditos** do Pikaso e onde estão os arquivos editáveis.
- **Sempre termine com a descrição pronta para postar** (o usuário copia e cola), num bloco de texto próprio:
  1. primeira linha com gancho forte (é o que aparece antes do "mais");
  2. 2 a 4 linhas curtas resumindo o conteúdo, com 1 ou 2 emojis no máximo por linha;
  3. CTA em pergunta para puxar comentário (o mesmo do final do vídeo);
  4. fontes/créditos quando houver fotos ou dados ("Fonte: G1, Folha. Fotos: Reuters, Wikimedia Commons");
  5. de 5 a 10 hashtags do tema e do nicho, em português, misturando grandes e específicas.
  Salve também como `descricao.txt` na pasta do projeto.

## Fotos reais de figuras públicas (sempre em assuntos públicos)
O usuário quer **ver as pessoas da notícia**: em todo assunto público (escândalos, política, empresas, famosos,
esporte, crimes noticiados), use fotos reais de cada figura central. Isso torna o vídeo crível e reconhecível.
1. **Wikimedia Commons primeiro** (licença livre): `python3 buscar_fotos.py wiki "Nome Sobrenome"`. Escolha retrato nítido e recente.
2. **Fotos da cobertura jornalística**, para quem não está no Commons ou para a foto *do fato* (ex.: o encontro, o evento):
   `python3 buscar_em_alta.py g1 "palavras"` para achar a matéria e `python3 buscar_fotos.py g1 URL` para listar as fotos com legenda e agência.
   Use só fotos cuja legenda identifique a pessoa ou o fato.
3. Baixe com `python3 buscar_fotos.py baixar URL assets/foto_nome.jpg` e **confira a foto** (Read numa miniatura) antes de usar.
4. Na tela: **crédito sempre visível** no canto inferior ("Foto: Reuters", "Foto: autor / Wikimedia Commons (CC BY-SA 4.0)"),
   trocado conforme a foto da cena. No texto final ao usuário, avise que fotos de agência têm direitos autorais
   (uso jornalístico/comentário) e que as do Commons exigem o crédito.
5. Recursos que valorizam a foto: polaroid com nome em Anton, círculo vermelho desenhado à mão em volta da pessoa,
   etiqueta com o nome, segunda foto entrando por cima quando a outra pessoa é citada.
6. Limites (protegem o usuário): **nunca** gerar ou alterar com IA o rosto ou a cena de uma pessoa real (montagem
   fabricada engana o público); não usar fotos de menores de idade nem de vítimas; quem é só *suspeito* recebe a
   legenda "suposta/suspeita", nunca "culpada".

## Quando o pedido for "analisar / decupar / recriar um vídeo de referência"
- Use `ffprobe` (duração, fps, áudio), detecção de cena (`select='gt(scene,0.3)',showinfo`) e folhas de frames
  (`fps=2` ou `fps=10` com `drawtext` do timestamp, `tile`).
- Produza uma tabela por cena (tempo, visual, texto, técnica) e o "DNA" do estilo, salvando em `DECUPAGEM.md`.
- Para **não ficar igual** (engenharia reversa): mantenha a estrutura e a mensagem, mas troque paleta, fontes,
  enquadramento e transições usando outro estilo do catálogo. Reaproveite do original só o conteúdo do usuário.

## Preferências do usuário (lembre-se)
- Entrega finalizada, sem perguntas intermediárias desnecessárias.
- Duração livre quando necessário: vídeos mais longos e explicativos (60–90 s, até ~3 min) são permitidos se o tema pedir.
- Sempre efeitos sonoros **e** música de fundo combinando com o tema. **Música do banco de músicas, não gerada.**
- Pikaso no menor custo (ou no ilimitado, se um dia aparecer como ilimitado no `simulate_cost`).
- Voz Caio Nogueira reprovada. Camila Rocha aprovada (também funciona bem em notícia/escândalo). Joana Cordeiro fala devagar: com ela, o roteiro de cerca de 110 palavras deu 68 s.
- Assuntos públicos: sempre fotos reais das figuras públicas, com crédito na tela.
- **Quebra de texto e espaçamento impecáveis**: `--check` com LAYOUT OK em todo vídeo, inclusive depois de qualquer ajuste.
  Nem apertado **nem espaçado demais**: os últimos vídeos ficaram com muito espaço entre os textos.
- Sempre capriche: animações bonitas como nas referências do Pinterest.
- Narração revisada: corrigir qualquer erro de pronúncia ou palavra errada antes de animar.
- Recortes de imagem sempre que a cena pedir (objetos e pessoas soltos, colagens, camadas).
- Todo vídeo termina com a descrição pronta para postar (legenda + CTA + hashtags).
