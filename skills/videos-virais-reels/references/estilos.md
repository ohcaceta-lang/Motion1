# Catálogo de estilos

Escolha **um** estilo por vídeo, conforme o tom do tema. Cada estilo tem paleta, fontes, recursos de cena,
transições e sons que funcionam juntos. Os nomes das fontes são as famílias carregadas pelo `lib.js`
(`FONTS.sans/serif/caps/type/hand/dms`).

O DNA comum de todos (é o que faz o vídeo "parecer de editor"):
1. Texto **palavra por palavra no tempo da voz**, com a palavra-chave 1,8–2,5× maior, em outra fonte e/ou cor.
2. **Uma imagem central por frase**, com sombra ou vinheta.
3. **A câmera nunca para**: zoom lento contínuo (2–5% por cena) e entradas com overshoot (`backOut`/`pop`).
4. **Transições motivadas**: círculo que engole a tela, zoom para dentro de um objeto, flash, blur com giro, mancha.
5. Grão e vinheta por cima de tudo.
6. Roteiro: gancho → contexto (data/nome) → virada → revelação → CTA em forma de pergunta.

---

## 1. True crime / mistério (dark editorial)
- **Quando usar:** crimes, escândalos, investigações, espionagem, casos policiais, "o lado sombrio de…".
- **Paleta:** preto `#000`, vermelho-sangue `#e3141b`, osso `#efe6d6`.
- **Fontes:** Inter 600 nas palavras de ligação, Playfair 900 itálico nas palavras-chave, Anton em carimbos e números, Special Elite (`type`) em datas datilografadas, Caveat (`hand`) em anotações.
- **Cenas que funcionam:** relógio ("um dia", "anos depois"), papel datilografado com a data, cômodo vazio com tinta vermelha por cima (multiply), dossiê com cartões, alfinetes e **fio vermelho** (stroke-dashoffset), carimbo "CONDENADO/CONFIRMADO" (filtro `#rough`), contador grande sobre grades, citação com aspas gigantes e **glitch RGB**, bolhas de comentários com 😡, enquete SIM/NÃO.
- **Transições:** flash vermelho, blur com escurecimento, cintilação ("ela fala").
- **Som:** música com drone grave, pulso de coração e piano esparso (Lyria). Efeitos: `ticks`, `typing` + `bell`, `stamp`, `impact`, `clang`, `riser` antes da citação, `glitch`, `pop` nas bolhas.
- **Voz:** Joana Cordeiro (feminina, indicada para true crime).

## 2. Lifestyle / bem-estar / vida real (quente e orgânico)
- **Quando usar:** famosos mudando de vida, viagens, casa, natureza, comida, rotina, histórias inspiradoras.
- **Paleta:** creme `#fbf3e4`, verde-mata `#2f5d3a`, laranja-pôr-do-sol `#f08a24`, tinta `#2a2118`.
- **Fontes:** DM Serif Display (normal e itálico) para nomes e palavras-chave, Caveat em frases afetivas, Anton em números, Inter nas ligações.
- **Cenas que funcionam:** cidade cinza que "sobe" com blur e revela a natureza, mapa de papel com curvas de nível e **alfinete caindo** com quique, planta (blueprint) desenhada linha a linha com contador de m², polaroids entrando girando, etiqueta de preço pendurada balançando, citação na golden hour, enquete com dois cartões (🏙️ × 🌄) e barras.
- **Som:** folk acústico com violão dedilhado (Lyria). Efeitos: `city` + `muffle` no começo, `chime` na revelação, `birds`, `scratch` (lápis), `pin_drop`, `ticks` no contador, `kaching` no preço, `crickets` à noite.
- **Voz:** Camila Rocha (feminina, doce e envolvente). Evite Caio Nogueira: o usuário achou feia.

## 3. Kinetic minimal (motivacional / negócios / marketing)
*Referência: "Kinetic Typography Reel".*
- **Paleta:** alterna creme `#f7f3ec` e preto puro, com vermelho `#e3141b` nos destaques.
- **Fontes:** Inter 500/600, com a palavra-chave 1,5× maior, em vermelho e com glow no fundo escuro.
- **Cenas:** objeto 3D ou emoji central (lâmpada, maleta, teclado), arco cinza grosso atravessando a tela, emojis gigantes cortados nos cantos, cartão "pendurado" com alfinete e lista de itens com ícones, homem de terno em halftone com cabeça de círculo branco onde o texto entra.
- **Transições:** **bola preta que cresce e engole a tela**, círculo translúcido varrendo a tela, giro com blur, flash branco entre preto e creme.
- **Ritmo:** nova cena a cada ~1,5 s e nova palavra a cada 0,2–0,4 s.

## 4. Arquivo histórico monocromático (biografias)
*Referência: "Thomas Edison".*
- **Paleta:** tudo em cinza; fundo de papel com carta manuscrita e texto datilografado em baixa opacidade.
- **Fontes:** sans pesada cinza-escura combinada com palavras pequenas em fonte fina, e marca-texto cinza atrás de uma palavra.
- **Cenas:** fotos de arquivo P&B com **sombra difusa grande**, foto que "sai" da moldura, setas e círculos desenhados à mão (trim path), assinatura sobreposta, fotos presas com fita trocando rápido no final.
- **Transições:** rack focus (foto desfocada que entra em foco), letras gigantes de fundo em baixa opacidade.

## 5. Colagem editorial vermelha (crítica / polêmica / denúncia)
*Referência: "Pin'em – Aging".*
- **Paleta:** vinho `#5a0a0e` → `#2a0505`, creme `#e8dcc4`, com vinheta pesada.
- **Fontes:** serifada display condensada (Playfair 900 ou Anton).
- **Cenas:** recortes em **halftone/xilogravura** (classe `.ht` + `grayscale`), interrogações gigantes orbitando, faixa vermelha ondulada usada como máscara, linhas tracejadas desenhadas, contador de datas, glitch com RGB split, objetos em loop (tubo espremendo, moedas orbitando).
- Regra de ouro: **todo asset recebe o mesmo tratamento** (halftone + duotone vermelho), o que unifica imagens de origens diferentes.

## 6. Cinemático com cenas de IA (histórias de invenções e curiosidades)
*Referências: "Pin'em – The Scream" e "Pin'em – Escova de dentes".*
- **Paleta:** âmbar/sépia nas cenas de época e cinza-azulado nas cenas frias.
- **Fontes:** serifada itálica bold vermelha ou amarela no gancho, sans arredondada creme nos títulos, serif itálico fino nas palavras soltas.
- **Cenas:** imagens fotorrealistas de época (geradas no Pikaso) com parallax, quadro/polaroid caindo e quicando, etiqueta de papel rasgado, palavras espalhadas em **profundidade 3D** convergindo, palavras em escada diagonal, TV CRT com texto em cores RGB saturadas, barra de busca com digitação no CTA.
- **Transições:** fumaça, zoom para dentro do quadro, máscara de pincelada, canhões de luz acendendo.

---

## Tamanhos que funcionam (canvas 720×1280, exportado em 1080×1920)
- Palavras de ligação: 40–56 px (Inter 600).
- Palavra-chave: 70–150 px (serif/DM Serif/Anton).
- Largura máxima de uma linha: 640 px (margem de 40 px de cada lado). Quebre em mais linhas em vez de encolher a fonte.
- Espaço vertical entre centros de linhas do mesmo bloco: **de 1,1 a 1,3 × a maior fonte das duas** (ex.: fontes de 74 px → centros entre 81 e 96 px). Mais que isso deixa o texto solto, com buracos (o `--check` acusa `ESPAÇADO`).
- A frase inteira deve formar **um bloco compacto** perto da imagem a que se refere, e não linhas espalhadas pela tela.
- Confirme sempre com `node render.js video.html --check` (deve dar LAYOUT OK).
- Texto sobre foto: escureça com `shade()` (gradiente ou radial) para garantir leitura.
