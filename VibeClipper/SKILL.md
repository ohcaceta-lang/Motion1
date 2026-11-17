---
name: vibeclipper
description: Pega um vídeo longo do YouTube (podcast, live, entrevista, aula), assiste tudo pela transcrição, escolhe os melhores momentos com hook forte, corta na vertical (9:16) e edita cada corte (zoom no fim da frase em volta do rosto, legenda de 2 a 3 palavras com as palavras de ênfase em destaque, whoosh) e entrega os cortes prontos em 1080p, cada um com título, legenda pra postar e nota de 0 a 10. Ative em "roda a skill do VibeClipper nesse vídeo <link>", "corta esse vídeo", "faz cortes desse podcast", "/vibeclipper".
---

# VibeClipper

Você recebe um link do YouTube e devolve **cortes verticais prontos pra postar** (Shorts, Reels, TikTok), cada um com título,
legenda pra postar e nota de 0 a 10, em 1080x1920. Download, Whisper, corte e edição rodam no computador da pessoa, de graça. A
única parte que usa IA é a ESCOLHA dos momentos, e essa parte é você, lendo a transcrição.

São 4 etapas: **assiste** (baixa e transcreve), **escolhe** os melhores momentos, **corta** na vertical e **edita** cada um. A
pessoa só manda o link; você faz o resto sem perguntar nada, a não ser que falte o link.

## Antes de começar
- Rode tudo de dentro desta pasta. Se ainda não configurou, rode `python instalar.py` (no Mac e no Linux pode ser `python3`).
- **Python:** se existir a pasta `.venv` aqui, use o Python dela em todos os comandos (`.venv/Scripts/python` no Windows,
  `.venv/bin/python` no Mac e no Linux). Abaixo está escrito só `python`.
- **Pastas:** trabalhe em `trabalho/<slug-do-video>/` (crie; o slug é o título curto, sem acento nem espaço). Os cortes prontos
  vão pra `saida/<slug-do-video>/`. Abaixo, `T` = `trabalho/<slug>` e `O` = `saida/<slug>`.
- Os scripts mostram o que estão fazendo e param com uma mensagem clara se algo der errado. Leia a mensagem, conserte e siga.

## Etapa 1: assiste (baixa e transcreve)
```
python scripts/baixar.py "<link>" --pasta T
python scripts/transcrever.py T/audio.m4a --saida T/transcricao.json --prompt "<título do vídeo, do T/info.json>"
python scripts/escolher.py preparar T/transcricao.json --saida T/transcricao-numerada.md --titulo "<título>"
```
- O `baixar.py` diz no fim onde ficou o áudio (quase sempre `T/audio.m4a`; se vier outro, use o que ele disse).
- O Whisper roda local, na placa NVIDIA se tiver. Ele guarda o **timestamp de cada palavra**: é com ele que o corte começa na
  palavra exata, que o zoom cai no fim da frase e que cada legenda aparece e some na hora certa. **Na 1ª vez ele baixa o modelo**
  (uma vez só), então avise a pessoa que a primeira demora mais.
- **ElevenLabs (opcional):** se a pessoa pedir a transcrição da ElevenLabs, que é paga e ainda mais precisa, use
  `--motor elevenlabs`. A chave vai num arquivo `.env` nesta pasta, com a linha `ELEVENLABS_API_KEY=...` (peça pra pessoa criar o
  arquivo; nunca escreva a chave dela no chat). Sem pedido, é sempre o Whisper.
- Se o vídeo não for em português, troque `--idioma pt` (ex.: `--idioma en`).

## Etapa 2: escolhe (você)
Leia `T/transcricao-numerada.md` INTEIRO, do começo ao fim (em partes, se for grande). Procure momentos que:
1. **Funcionam sozinhos:** um estranho, uma pessoa qualquer que não viu o resto do vídeo e não tem o contexto, entende
   completamente.
2. **Abrem com um hook** dos que funcionam nos Shorts, no Instagram e no TikTok: um **fato surpreendente**, uma **afirmação
   controversa ou ousada**, ou o **começo de uma história**. TODO corte abre com um deles. Se logo antes do hook a fala está
   enrolando ("então, é, deixa eu pensar, como eu tava falando..."), pule a enrolação e comece EXATAMENTE no hook.
3. **Terminam na conclusão:** a última frase fecha o raciocínio. Nunca corte no meio do nada.
4. Têm de **30 a 75 segundos** e não dependem de nada mostrado na tela (gráfico, objeto) pra fazer sentido.
5. Não são propaganda, patrocínio, vinheta ou papo de bastidor.

**Quantos:** de 5 a 8 cortes num vídeo longo (padrão 7), sem repetir assunto. Em vídeo de menos de 20 minutos, de 2 a 4. Se a
pessoa pedir um número, use o número dela.

Dê a cada um uma **nota de 0 a 10** (força do hook + clareza sozinho + potencial de compartilhar) e escreva `T/escolha.json` no
formato de `T/escolha.modelo.json`:
- `titulo` (curto, 3 a 8 palavras), `legenda` (a legenda pra postar: 1 a 3 frases, sem hashtag), `nota`, `porque`,
  `hook_tipo` (`fato surpreendente` | `afirmação ousada` | `começo de história`);
- `linha_ini` (a linha do HOOK) e `linha_fim` (a linha da CONCLUSÃO); `pular_ini` / `cortar_fim` (quantas palavras tirar do
  começo da 1ª linha / do fim da última, se a frase começa ou termina com sobra);
- `hook_ate` (a linha onde a frase do hook termina, quando ela ocupa mais de uma linha);
- `enrolacao` (as linhas logo antes do hook que você pulou, ex. `"L0410-L0412"`, se tiver);
- `correcoes` (opcional): o que o Whisper ouviu errado DENTRO do corte e vai aparecer na legenda, como
  `[["a Ana Clara", "a Anna Klara"], ["2 .500 .000", "2.500.000"]]`. Só nome próprio, número quebrado e erro óbvio pelo contexto;
  na dúvida, deixe como está;
- `enfase`: 4 a 10 palavras (ou expressões curtas) que mais importam no corte, exatamente como estão na transcrição: números,
  valores, a palavra que vira o raciocínio. Elas ganham a cor na legenda (os números ganham sempre);
- `cor_marca` (no topo do arquivo): a cor da marca do criador, se a pessoa passou ou se ela é clara (logo, vinheta). Se ninguém
  passou e não tem marca clara, deixe `null`: a skill puxa do próprio vídeo uma cor que combina com a identidade dele.

Depois valide (ajusta o início e o fim na palavra exata e ordena pela nota, **o melhor sempre vem primeiro**):
```
python scripts/escolher.py validar T/escolha.json --transcricao T/transcricao.json --saida T/cortes.json
```
Se avisar duração fora de 30 a 75 s, ajuste as linhas e valide de novo.

## Etapa 3: corta (vertical)
```
python scripts/baixar.py "<link>" --pasta T --trechos T/cortes.json
python scripts/cortar.py --cortes T/cortes.json --trechos T/trechos --audio T/audio.m4a --pasta T
python scripts/enquadrar.py T/corte-N/fonte.mp4 --cortes T/cortes.json --n N --saida T/corte-N/plano.json   (pra cada N)
```
- O `baixar.py --trechos` baixa SÓ os trechos escolhidos, na melhor qualidade (até 4K), pro recorte vertical sair nítido.
- O `cortar.py` corta cada momento na palavra exata (com `--cru O/cru` ele grava também o momento cru no vídeo original, 16:9,
  pra comparar o antes e depois; só se a pessoa quiser).
- O `enquadrar.py` detecta cada troca de câmera, acha o rosto em cada cena (detecção de rosto) e centraliza a moldura 9:16 em
  quem está na tela, parada dentro da cena e recentralizada a cada troca (se a pessoa se inclina demais, a moldura acompanha
  devagar): ninguém fica cortado pela metade. Também marca os zooms no fim das frases, a cada poucos segundos, em volta do rosto.

## Etapa 4: edita e renderiza
Pra cada corte N:
```
python scripts/legendar.py --cortes T/cortes.json --n N --plano T/corte-N/plano.json --saida T/corte-N/legenda.ass
python scripts/efeitos.py --plano T/corte-N/plano.json --legenda T/corte-N/legenda.json --saida T/corte-N/sfx.json
python scripts/renderizar.py --fonte T/corte-N/fonte.mp4 --plano T/corte-N/plano.json --legenda T/corte-N/legenda.ass --sfx T/corte-N/sfx.json --saida O/corte-N.mp4
```
- A cor da legenda: a que a pessoa pedir (`--cor`), senão a da marca (`cor_marca`), senão a skill tira do próprio vídeo (dos
  trechos dos cortes) uma vez só e grava no `cortes.json`: a mesma cor em todos os cortes.
- O render sai em **1080p (1080x1920, Full HD)**, 30 fps, H.264 + AAC, com o áudio normalizado pra -14 LUFS.
- Dá pra rodar 2 cortes ao mesmo tempo pra ganhar tempo.

No fim, o resumo pra postar:
```
python scripts/escolher.py resumo T/cortes.json --saida O/cortes.md
```

## Entrega
Responda com a tabela: `#`, título, duração, nota, legenda pra postar, arquivo (`O/corte-N.mp4`). Diga a cor da legenda e de onde
ela veio, e que o resumo está em `O/cortes.md`.

## Ajustes que a pessoa pode pedir depois
Ela fala em português normal (às vezes começando com "Claudião", que é brincadeira). Refaça só o que mudou e entregue o arquivo
novo com a duração.
- **"tira só o melhor corte, deixa com menos de 30 segundos"**: copie o corte 1 do `T/escolha.json` pro
  `T/escolha-ajuste.json` (com o mesmo `cor_marca`), mesmo `linha_ini` (o mesmo hook), `linha_fim` numa conclusão anterior que
  feche abaixo de 30 s, e `"trecho": N` com o número que esse corte tem no `T/cortes.json` (pra reaproveitar o trecho já baixado).
  Depois:
  ```
  python scripts/escolher.py validar T/escolha-ajuste.json --transcricao T/transcricao.json --saida T/ajuste.json --min 15 --max 30
  python scripts/cortar.py --cortes T/ajuste.json --trechos T/trechos --audio T/audio.m4a --pasta T/ajuste
  python scripts/enquadrar.py T/ajuste/corte-1/fonte.mp4 --cortes T/ajuste.json --n 1 --saida T/ajuste/corte-1/plano.json
  python scripts/legendar.py --cortes T/ajuste.json --n 1 --plano T/ajuste/corte-1/plano.json --saida T/ajuste/corte-1/legenda.ass --cor "<cor>"
  python scripts/efeitos.py --plano T/ajuste/corte-1/plano.json --legenda T/ajuste/corte-1/legenda.json --saida T/ajuste/corte-1/sfx.json
  python scripts/renderizar.py --fonte T/ajuste/corte-1/fonte.mp4 --plano T/ajuste/corte-1/plano.json --legenda T/ajuste/corte-1/legenda.ass --sfx T/ajuste/corte-1/sfx.json --saida O/ajuste-1.mp4
  ```
  No `--cor`, use a que ela pediu ou, se não pediu cor nova, a mesma dos cortes (`cor_video.cor` ou `cor_marca` do `T/cortes.json`).
- **"sem efeito sonoro"**: `efeitos.py ... --sem`.
- **"bota a cor da legenda em azul" (ou outra cor)**: `legendar.py ... --cor "#2F7BFF"` (azul). Vermelho `#FF3B30`, verde
  `#22C55E`, amarelo `#FFD400`, rosa `#FF4FA3`, roxo `#8B5CF6`, ou o hex que ela mandar.
- **"zoom mais forte / mais fraco"**: `enquadrar.py ... --zoom 1.3` (ou `1.1`), depois legenda, efeitos e render de novo.
- **"faz mais cortes / menos cortes"**: volte na etapa 2, mexa no `T/escolha.json` e refaça daí pra frente só os cortes novos.
