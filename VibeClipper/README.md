# VibeClipper

Você cola um link do YouTube e o Claude Code te devolve os cortes verticais prontos pra postar, cada um com título, legenda e nota
de 0 a 10, sem pagar nenhuma assinatura de ferramenta de corte.

A skill passa por 4 etapas e faz tudo sozinha:

1. **Assiste:** baixa o áudio e transcreve o vídeo inteiro com o Whisper, guardando o momento exato em que cada palavra é dita.
2. **Escolhe:** o Claude lê a transcrição do começo ao fim e procura os momentos que um estranho entende sem contexto, que abrem
   com um hook forte e terminam na conclusão. Dá uma nota de 0 a 10 pra cada corte e faz o ranking, o melhor sempre primeiro.
3. **Corta:** baixa só esses trechos na melhor qualidade e enquadra na vertical em quem está falando, centralizando de novo a cada
   troca de câmera.
4. **Edita:** zoom no fim das frases em volta do rosto, legenda de 2 a 3 palavras por vez com as palavras de ênfase em destaque,
   whoosh nos zooms e render final em 1080p, Full HD.

## O que você precisa
- O **Claude Code** com uma assinatura do plano pago do Claude. Pode ser o de 20 dólares, ele já funciona bem.
- Um computador com Windows, Mac ou Linux. O resto (Python, ffmpeg, Whisper e as bibliotecas) o Claude configura pra você.
- Placa de vídeo NVIDIA é opcional: com ela o Whisper e o render ficam bem mais rápidos.

## Configurar (uma vez só)
1. Extraia o `VibeClipper.zip` (no Windows: botão direito, **Extrair Tudo**). Vai aparecer a pasta `VibeClipper`.
2. Abra o Claude Code, selecione a pasta `VibeClipper` e mande:

   > Claudão, você conseguiria configurar esse repositório inteiro pra mim?

3. Se ele pedir alguma permissão, é só clicar em **Permitir**. Se quiser, deixe no modo automático ou no ignorar permissões que
   ele executa tudo sem ficar perguntando, mas toma cuidado pra não excluir nada na sua máquina: nesse modo, assuma o seu risco.
4. Passados alguns minutos, ele te diz que a configuração terminou: **"A configuração terminou: o VibeClipper está pronto pra
   usar."** E é isso, essa parte você só faz uma vez.

Prefere rodar na mão? Abra o terminal na pasta e rode `python instalar.py`.

## Cortar um vídeo
No YouTube, clique em **Compartilhar** e copie o link. No Claude Code, aberto na pasta `VibeClipper`, mande:

> Roda a skill do VibeClipper nesse vídeo https://youtu.be/SEU_VIDEO

Esse já é o prompt completo. Na primeira vez demora um pouco mais, porque ele baixa o Whisper, que é o que transcreve o vídeo pra
ele editar tudo no tempo certo, e isso acontece uma vez só. Os cortes saem em `saida/<nome-do-video>/`, junto com o `cortes.md`,
que tem o título e a legenda pra postar de cada um.

## Ajustar depois
Quer alguma coisa diferente? É só pedir em português normal, por exemplo:

> Claudião, tira só o melhor corte, deixa com menos de 30 segundos e sem efeito sonoro. E bota a cor da legenda em azul.

O "Claudião" é zoeira, funciona sem ele. Também dá pra pedir "faz 5 cortes", "zoom mais forte" ou "usa a cor #FF3B30 na legenda".

## Como ele escolhe os momentos
- Lê a transcrição inteira e procura momentos que funcionam sozinhos, que uma pessoa qualquer, sem o contexto, entende
  completamente.
- Todo corte abre com um hook dos que funcionam nos Shorts, no Instagram e no TikTok: um fato surpreendente, uma afirmação
  controversa ou ousada, ou o começo de uma história. Se a fala tá dando uma enrolada antes, ele pula e começa exatamente no hook.
- O corte termina na conclusão, então tem sentido completo e nada fica pela metade.
- Cada corte ganha uma nota de 0 a 10 e o melhor sempre vem primeiro.

## Como ele edita
- **Legenda:** o Whisper guarda o timestamp de cada palavra, e é assim que cada legenda aparece e some na hora certa, com só 2 ou 3
  palavras na tela por vez e as palavras de ênfase em destaque.
- **Zoom:** a detecção de rosto acha o rosto em cada cena, e o zoom entra no fim de uma frase, a cada poucos segundos, sem cortar
  nada importante. A cada troca de câmera o enquadramento muda junto, nada brusco.
- **Cor da legenda:** primeiro a cor da marca do criador, se você disser qual é. Se não disser, ele puxa do próprio vídeo uma cor
  que combina com a identidade dele.
- **Som:** os whooshes e o pop que vêm na pasta `sons/`.
- **Render:** 1080x1920 (Full HD), pronto pra postar.

## Whisper ou ElevenLabs
O Whisper é gratuito, roda no seu computador e resolve tranquilo. Se você quiser uma transcrição ainda mais precisa, dá pra usar o
ElevenLabs, que é pago: crie um arquivo `.env` nesta pasta com a linha `ELEVENLABS_API_KEY=sua_chave` e peça "usa o ElevenLabs
pra transcrever". Não é obrigatório.

## Quanto custa
A skill não usa crédito nenhum. O download, o Whisper, o corte e a edição rodam no seu computador, totalmente de graça. A única
parte que usa IA é quando o Claude escolhe os momentos, e isso roda no mesmo plano do Claude que você já paga.

## O que tem na pasta
```
VibeClipper/
  SKILL.md            o passo a passo que o Claude segue
  CLAUDE.md           o que o Claude faz quando você pede pra configurar ou cortar
  README.md           este arquivo
  instalar.py         confere e instala tudo
  scripts/
    baixar.py         baixa o áudio e, depois, só os trechos escolhidos (yt-dlp)
    transcrever.py    Whisper local (ou ElevenLabs) com o tempo de cada palavra
    escolher.py       prepara a transcrição numerada, valida a escolha do Claude e faz o resumo pra postar
    cortar.py         corta cada momento na palavra exata
    enquadrar.py      troca de câmera, detecção de rosto, moldura 9:16 e zooms
    legendar.py       legenda de 2 a 3 palavras com destaque e a cor
    efeitos.py        whoosh nos zooms, pop nos destaques
    renderizar.py     render final 1080x1920, H.264 + AAC
    comum.py          o que todo script faz antes de começar
  sons/
    gerar_sons.py     gera os sons por código
    whoosh.wav, whoosh-2.wav, pop.wav
```

## Bom saber
- Use em vídeos seus ou que você tem autorização pra cortar.
- Os sons foram gerados por código (`sons/gerar_sons.py`), então são seus: pode usar, mudar e distribuir à vontade.
- O detector de rosto é o YuNet do OpenCV Zoo (licença MIT) e a fonte da legenda é a Montserrat (licença SIL OFL). Os dois o
  `instalar.py` baixa na configuração.
