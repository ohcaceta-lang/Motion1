"""VibeClipper, etapa 1 (assiste): transcreve o áudio inteiro com o tempo de cada palavra.

O Whisper não só escreve o que foi falado: ele guarda o timestamp de cada palavra (início e fim). É com esse tempo que a
escolha acha o hook exato, que o zoom cai no fim da frase e que cada legenda aparece e some na hora certa.

uso:
  python scripts/transcrever.py trabalho/audio.m4a --saida trabalho/transcricao.json [--modelo turbo] [--idioma pt]
                                [--prompt "nomes próprios do vídeo"]

Dois motores:
  - whisper (padrão): o Whisper LOCAL (faster-whisper), grátis, nada sai do computador. Roda na placa de vídeo NVIDIA se tiver
    (float16); senão no processador (int8, mais lento). Na 1ª vez baixa o modelo (o turbo tem ~1,6 GB), uma vez só.
  - elevenlabs (opcional, pago): --motor elevenlabs manda o áudio pro Speech to Text da ElevenLabs, que é ainda mais
    preciso. Precisa da chave da API: variável ELEVENLABS_API_KEY ou um arquivo .env na pasta da skill com a linha
    ELEVENLABS_API_KEY=sua_chave. A saída é a mesma, então o resto da skill funciona igual.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
FIM_FRASE = re.compile(r"[.!?…]['\")»]*$")


def preparar_cuda():
    """No Windows, o faster-whisper precisa achar as DLLs do cuBLAS e do cuDNN (pacotes pip nvidia-*). Põe as pastas no PATH."""
    if os.name != "nt":
        return
    for nome in ("nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_nvrtc", "nvidia.cuda_runtime"):
        try:
            mod = __import__(nome, fromlist=["x"])
        except ImportError:
            continue
        for base in list(getattr(mod, "__path__", [])):
            pasta = os.path.join(base, "bin")
            if os.path.isdir(pasta):
                os.environ["PATH"] = pasta + os.pathsep + os.environ.get("PATH", "")
                try:
                    os.add_dll_directory(pasta)
                except OSError:
                    pass


def carregar_modelo(modelo="turbo"):
    preparar_cuda()
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")   # aviso do Windows sem importância (o download funciona)
    from faster_whisper import WhisperModel
    try:
        m = WhisperModel(modelo, device="cuda", compute_type="float16")
        return m, "cuda/float16"
    except Exception as e:  # sem GPU ou sem CUDA: cai pro processador
        print(f"[transcrever] placa de vídeo indisponível ({str(e)[:80]}), usando o processador", file=sys.stderr)
        return WhisperModel(modelo, device="cpu", compute_type="int8"), "cpu/int8"


def ler_audio(caminho, sr=16000):
    """Decodifica qualquer áudio/vídeo com o ffmpeg em mono 16 kHz (o formato do Whisper)."""
    import numpy as np
    b = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", caminho, "-vn", "-ac", "1", "-ar", str(sr),
                        "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).copy()


def transcrever(audio, modelo="turbo", idioma="pt", prompt=None):
    audio = ler_audio(audio)
    m, disp = carregar_modelo(modelo)
    try:
        segs, info = m.transcribe(audio, language=idioma, word_timestamps=True, beam_size=5, vad_filter=True,
                                  condition_on_previous_text=False, initial_prompt=prompt)
        segs = list(segs)
    except RuntimeError as e:
        if not disp.startswith("cuda"):
            raise
        print(f"[transcrever] erro na placa de vídeo ({str(e)[:80]}), refazendo no processador", file=sys.stderr)
        from faster_whisper import WhisperModel
        m, disp = WhisperModel(modelo, device="cpu", compute_type="int8"), "cpu/int8"
        segs, info = m.transcribe(audio, language=idioma, word_timestamps=True, beam_size=5, vad_filter=True,
                                  condition_on_previous_text=False, initial_prompt=prompt)
        segs = list(segs)
    saida = {"modelo": f"faster-whisper {modelo} ({disp})", "idioma": info.language, "duracao": round(info.duration, 2),
             "segmentos": []}
    for s in segs:
        palavras = [{"p": w.word.strip(), "ini": round(float(w.start), 3), "fim": round(float(w.end), 3),
                     "prob": round(float(w.probability), 3)} for w in (s.words or []) if w.word.strip()]
        saida["segmentos"].append({"ini": round(float(s.start), 3), "fim": round(float(s.end), 3),
                                   "texto": s.text.strip(), "palavras": palavras})
    return saida


# --- ElevenLabs (opcional) -------------------------------------------------------------------------------------------

def chave_elevenlabs():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"].strip()
    for env in (os.path.join(AQUI, "..", ".env"), os.path.join(os.getcwd(), ".env")):
        if os.path.exists(env):
            for linha in open(env, encoding="utf-8"):
                k, _, v = linha.strip().partition("=")
                if k.strip() == "ELEVENLABS_API_KEY" and v.strip():
                    return v.strip().strip('"').strip("'")
    raise SystemExit("[transcrever] falta a chave da ElevenLabs: crie um arquivo .env na pasta da skill com a linha "
                     "ELEVENLABS_API_KEY=sua_chave (ou use o Whisper, que é grátis: tire o --motor elevenlabs)")


def duracao_de(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def segmentos_de_palavras(pal, pausa=0.8, max_pal=40):
    """Junta as palavras soltas em segmentos (frase terminada, pausa longa ou 40 palavras), no formato do Whisper."""
    segs, at = [], []
    for i, w in enumerate(pal):
        at.append(w)
        prox = pal[i + 1] if i + 1 < len(pal) else None
        if prox is None or FIM_FRASE.search(w["p"]) or prox["ini"] - w["fim"] >= pausa or len(at) >= max_pal:
            segs.append({"ini": at[0]["ini"], "fim": at[-1]["fim"], "texto": " ".join(x["p"] for x in at), "palavras": at})
            at = []
    return segs


def transcrever_elevenlabs(audio, idioma="pt", modelo="scribe_v2"):
    import urllib.error
    import urllib.request
    fronteira = uuid.uuid4().hex
    campos = {"model_id": modelo, "timestamps_granularity": "word", "tag_audio_events": "false", "diarize": "false"}
    if idioma:
        campos["language_code"] = idioma
    corpo = b"".join(f"--{fronteira}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in campos.items())
    nome = os.path.basename(audio)
    corpo += (f"--{fronteira}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{nome}\"\r\n"
              f"Content-Type: application/octet-stream\r\n\r\n").encode()
    corpo += open(audio, "rb").read() + f"\r\n--{fronteira}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=corpo, method="POST",
                                 headers={"xi-api-key": chave_elevenlabs(),
                                          "Content-Type": f"multipart/form-data; boundary={fronteira}"})
    try:
        with urllib.request.urlopen(req, timeout=3600) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"[transcrever] a ElevenLabs recusou ({e.code}): {e.read().decode('utf-8', 'replace')[:400]}")
    pal = []
    for w in d.get("words", []):
        if w.get("type") != "word" or w.get("start") is None or not str(w.get("text", "")).strip():
            continue
        prob = math.exp(w["logprob"]) if isinstance(w.get("logprob"), (int, float)) else 1.0
        pal.append({"p": w["text"].strip(), "ini": round(float(w["start"]), 3), "fim": round(float(w["end"]), 3),
                    "prob": round(prob, 3)})
    return {"modelo": f"ElevenLabs {modelo}", "idioma": d.get("language_code", idioma),
            "duracao": round(duracao_de(audio) or (pal[-1]["fim"] if pal else 0.0), 2),
            "segmentos": segmentos_de_palavras(pal)}


def palavras(transcricao):
    """Lista plana de palavras [{p, ini, fim}] (usada pelas outras etapas)."""
    return [w for s in transcricao["segmentos"] for w in s["palavras"]]


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import comum
    comum.preparar()                                       # UTF-8 no terminal e o ffmpeg no PATH
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--motor", choices=["whisper", "elevenlabs"], default="whisper")
    ap.add_argument("--modelo", default=None,
                    help="whisper: turbo (padrão, large-v3-turbo, ~1,6 GB), medium, small, base, large-v3; "
                         "elevenlabs: scribe_v2 (padrão)")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--prompt", default=None, help="contexto opcional pro Whisper (título do vídeo, nomes próprios)")
    a = ap.parse_args()
    t0 = time.time()
    if a.motor == "elevenlabs":
        r = transcrever_elevenlabs(a.audio, a.idioma, a.modelo or "scribe_v2")
    else:
        r = transcrever(a.audio, a.modelo or "turbo", a.idioma, a.prompt)
    r["segundos_gastos"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.saida)), exist_ok=True)
    with open(a.saida, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    n = sum(len(s["palavras"]) for s in r["segmentos"])
    print(f"[transcrever] {len(r['segmentos'])} segmentos, {n} palavras, {r['duracao'] / 60:.1f} min de áudio "
          f"em {r['segundos_gastos'] / 60:.1f} min ({r['modelo']}) -> {a.saida}")


if __name__ == "__main__":
    main()
