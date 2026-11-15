# Google Flow (imagens e clipes de B-roll) — roda no PC do usuário

Skill externa: https://github.com/BRPLia/google-flow-skill-v1 (código v2). Controla o Google Flow no Chrome
via Playwright e baixa os arquivos. **Não roda na sessão em nuvem** (precisa do Chrome com o login do usuário).
Instalada e testada em 15/11/2026 no PC do usuário (Windows, Python 3.15):

- Pasta: `C:\Users\Luisão\google-flow-skill-v1\google-flow-skill-v1` (atenção: pasta dentro de pasta com o mesmo nome).
  Todo comando começa com `cd` para essa pasta, no PowerShell.
- Instalação: `python setup.py` → `python flow.py login` (o usuário entra na conta Google no Chrome que abre).
- **Ajuste de idioma obrigatório:** a conta Google está em português e a skill só reconhece a interface em espanhol/inglês
  (erro típico: `Timeout 45000ms ... Proyecto nuevo|Nuevo proyecto|New project`). Corrige com
  `scripts/flow/patch_idioma.py` (copiar para a pasta da skill e rodar `python patch_idioma.py`). Ele força
  `--lang=es-419`, `locale="es-419"` e a URL `https://flow.google.com/?hl=es-419`. Refazer se baixar a skill de novo.
- Diagnóstico sem gastar créditos: `scripts/flow/diag.py` → `python diag.py` (deve listar "add Proyecto nuevo").
- Testado: imagem única (`outputs\teste.png`) e lote `examples/lote_imagenes.json` 3/3 OK, ~8 s por imagem.
  O arquivo sai com extensão `.png`, mas é JPG 1K; tudo bem para o vídeo.

## Como usar num vídeo (divisão de trabalho)
1. Na nuvem: roteiro, cenas e um `videos/<slug>/flow/lote.json` com os cenários, objetos e B-roll de cada cena
   (prompts em inglês, completos e independentes, `9:16`). Cole o JSON também na resposta.
2. No PC: o usuário salva como `lote.json` na pasta da skill (`notepad lote.json`) e roda `python flow.py batch lote.json`.
3. Os arquivos saem em `outputs\<project>\`. O usuário faz commit deles em `videos/<slug>/assets/` (ou envia),
   e a animação/render segue normalmente com `lib.js`/`render.js`.

Formato do lote (um arquivo por job; `count > 1` é rejeitado):
```json
{
  "project": "<slug>",
  "defaults": {"ratio": "9:16", "image_model": "Nano Banana 2 Lite", "video_model": "Veo 3.1 - Lite"},
  "jobs": [
    {"type": "image", "name": "cena01_cenario", "prompt": "Complete self-contained prompt, vertical 9:16"},
    {"type": "video", "name": "cena01_clip", "start": "cena01_cenario", "prompt": "Slow push-in, light dust in the air"}
  ]
}
```
- Modelos: imagem `Nano Banana 2 Lite` (mais barato, padrão), `Nano Banana 2.1`, `Nano Banana Pro`;
  vídeo `Veo 3.1 - Lite` (sem escolha de duração) ou `Omni 1.2 Flash` (`duration`, cobra por segundo).
  Em 5/12/2026 o Flow retira `Omni 1.1 Flash`, `Veo 3.1 - Fast` e `Veo 3.1 - Quality`.
- Gasta créditos do Google Flow do usuário: manter o menor custo (Nano Banana 2 Lite / Veo 3.1 Lite) e só o necessário.
- Regra 6 continua valendo: **nunca gerar rostos de pessoas reais**; Flow só para cenários, objetos, metáforas e B-roll.
- Para recortes (fundo transparente), gere com "isolated on plain white background" e recorte no Pikaso
  (`images_remove_background`) depois de enviar com `creations_upload_image`.
