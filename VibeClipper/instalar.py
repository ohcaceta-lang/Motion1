"""VibeClipper: confere e instala tudo o que a skill precisa (rode uma vez só).

  python instalar.py            # confere e instala o que falta
  python instalar.py --conferir # só confere, não instala nada

O que ele confere:
  - Python 3.10 ou mais novo;
  - ffmpeg e ffprobe (cortar, legendar e renderizar o vídeo); se faltar, ele diz o comando pra instalar;
  - as bibliotecas do Python: yt-dlp com o deno (baixar do YouTube), faster-whisper (transcrever), opencv-python (detecção de
    rosto), numpy e pillow. O yt-dlp é sempre atualizado, porque o YouTube muda direto;
  - a placa de vídeo NVIDIA (se tiver, o Whisper e o render ficam bem mais rápidos) e, no Windows, as bibliotecas CUDA
    que o Whisper usa (nvidia-cublas-cu12 e nvidia-cudnn-cu12);
  - o modelo de detecção de rosto (YuNet, do OpenCV Zoo, licença MIT) em ~/.cache/vibeclipper;
  - uma fonte forte pra legenda: se não tiver a Montserrat, baixa a Montserrat Black (grátis, licença SIL OFL) em
    ~/.cache/vibeclipper/fontes.
O modelo do Whisper (turbo, ~1,6 GB) baixa sozinho na primeira transcrição.
Se o pip do sistema não deixar instalar (Mac ou Linux com o Python do sistema), ele cria um ambiente só da skill em .venv.
"""
import argparse
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
LIBS = [("faster_whisper", "faster-whisper"), ("cv2", "opencv-python"), ("numpy", "numpy"), ("PIL", "pillow")]
YTDLP = "yt-dlp[default,deno]"
CUDA_WIN = [("nvidia.cublas", "nvidia-cublas-cu12"), ("nvidia.cudnn", "nvidia-cudnn-cu12>=9,<10")]
YUNET = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
         "face_detection_yunet_2023mar.onnx")
MONTSERRAT = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "vibeclipper")


def ok(msg):
    print(f"  [ok] {msg}")


def falta(msg):
    print(f"  [falta] {msg}")


def tem(mod):
    try:
        return importlib.util.find_spec(mod) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def pip(pacotes):
    """pip install; se o Python do sistema for 'externally managed', cria o .venv da skill e roda o instalar.py nele."""
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", *pacotes], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode == 0:
        importlib.invalidate_caches()                     # pra enxergar o que acabou de instalar
        return
    erro = r.stdout[-2000:] + r.stderr[-2000:]
    if "externally-managed-environment" in erro and not os.environ.get("VIBECLIPPER_VENV"):
        venv = os.path.join(AQUI, ".venv")
        print(f"\n  o Python do sistema não deixa instalar biblioteca: criando um ambiente só da skill em {venv}")
        subprocess.run([sys.executable, "-m", "venv", venv], check=True)
        py = os.path.join(venv, "Scripts" if os.name == "nt" else "bin", "python")
        env = {**os.environ, "VIBECLIPPER_VENV": "1"}
        sys.exit(subprocess.run([py, os.path.abspath(__file__), *sys.argv[1:]], env=env).returncode)
    print(erro)
    raise SystemExit(f"[instalar] o pip não conseguiu instalar: {' '.join(pacotes)}")


def tem_deno():
    exe = "deno" + (sysconfig.get_config_var("EXE") or "")
    return os.path.isfile(os.path.join(sysconfig.get_path("scripts"), exe)) or shutil.which("deno") is not None


def baixar(url, destino, rotulo):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    print(f"\n  baixando {rotulo}")
    tmp = destino + ".parcial"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, destino)


def main():
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args()
    problemas = []
    print("VibeClipper: conferindo o computador\n")

    v = sys.version_info
    if v >= (3, 10):
        ok(f"Python {v.major}.{v.minor}.{v.micro} ({sys.executable})")
    else:
        falta(f"Python {v.major}.{v.minor}: precisa do 3.10 ou mais novo (python.org)")
        problemas.append("python")

    sys.path.insert(0, os.path.join(AQUI, "scripts"))
    from comum import achar_ffmpeg
    pasta_ff = achar_ffmpeg()
    for prog in ("ffmpeg", "ffprobe"):
        if pasta_ff:
            ok(f"{prog} ({pasta_ff})")
        else:
            dica = {"Windows": "winget install --id Gyan.FFmpeg -e", "Darwin": "brew install ffmpeg"}.get(
                platform.system(), "sudo apt install ffmpeg")
            falta(f"{prog}: instale com `{dica}` e rode o instalar.py de novo")
            problemas.append(prog)

    if not a.conferir:
        print(f"\n  instalando/atualizando: {YTDLP} " + " ".join(p for m, p in LIBS if not tem(m)))
        pip([YTDLP] + [p for m, p in LIBS if not tem(m)])
    for mod, pac in [("yt_dlp", "yt-dlp"), ("yt_dlp_ejs", "yt-dlp-ejs")] + LIBS:
        if tem(mod):
            ok(pac)
        else:
            falta(pac)
            problemas.append(pac)
    if tem_deno():
        ok("deno (o yt-dlp usa pra ler o YouTube)")
    else:
        falta(f'deno: rode `"{sys.executable}" -m pip install --upgrade "{YTDLP}"`')
        problemas.append("deno")

    gpu = None
    if shutil.which("nvidia-smi"):
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True,
                           text=True)
        gpu = r.stdout.strip().splitlines()[0] if r.returncode == 0 and r.stdout.strip() else None
    if gpu:
        ok(f"placa de vídeo NVIDIA: {gpu} (o Whisper e o render rodam na placa)")
        if platform.system() == "Windows":
            fc = [pac for mod, pac in CUDA_WIN if not tem(mod)]
            if fc and not a.conferir:
                print(f"\n  instalando as bibliotecas CUDA do Whisper (uma vez só, ~1 GB): {' '.join(fc)}")
                pip(fc)
                fc = [pac for mod, pac in CUDA_WIN if not tem(mod)]
            for mod, pac in CUDA_WIN:
                (falta if pac in fc else ok)(pac)
    else:
        ok("sem placa NVIDIA: o Whisper roda no processador (mais lento, mas funciona)")

    modelo = os.path.join(CACHE, "face_detection_yunet_2023mar.onnx")
    if not os.path.exists(modelo) and not a.conferir:
        try:
            baixar(YUNET, modelo, "o modelo de detecção de rosto (YuNet, 230 KB)")
        except OSError as e:
            print(f"  não deu pra baixar o YuNet ({e})")
    if os.path.exists(modelo):
        ok(f"detecção de rosto: YuNet ({modelo})")
    else:
        falta("modelo YuNet (sem ele a skill usa o detector Haar do OpenCV, que erra mais de perfil)")

    try:
        from legendar import achar_fonte
        try:
            arq, nome = achar_fonte()
        except SystemExit:
            arq, nome = None, ""
        if "Montserrat" not in nome and not a.conferir:
            try:
                baixar(MONTSERRAT, os.path.join(CACHE, "fontes", "Montserrat-Black.ttf"),
                       "a fonte da legenda (Montserrat Black, grátis, licença SIL OFL)")
                arq, nome = achar_fonte()
            except OSError as e:
                print(f"  não deu pra baixar a Montserrat ({e}): a legenda usa outra fonte forte do computador")
        if arq:
            ok(f"fonte da legenda: {nome} ({arq})")
        else:
            falta("fonte forte pra legenda: instale a Montserrat (grátis, fonts.google.com/specimen/Montserrat)")
            problemas.append("fonte")
    except ImportError as e:
        falta(f"não consegui carregar o legendar.py ({e})")
        problemas.append("bibliotecas")

    print()
    if problemas:
        print("Falta resolver: " + ", ".join(problemas))
        sys.exit(1)
    if os.environ.get("VIBECLIPPER_VENV"):
        print(f"Importante: rode os scripts com o Python do ambiente da skill: {sys.executable}")
    print("A configuração terminou: o VibeClipper está pronto pra usar.")
    print('No Claude Code, nesta pasta: "Roda a skill do VibeClipper nesse vídeo <link do YouTube>"')


if __name__ == "__main__":
    main()
