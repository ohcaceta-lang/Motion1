"""VibeClipper: o que todo script faz antes de começar (importado pelos outros, não precisa rodar sozinho).

  - acento e símbolo sem quebrar no terminal do Windows (a saída sai em UTF-8);
  - acha o ffmpeg mesmo quando ele acabou de ser instalado e o terminal ainda não enxerga (Windows: a pasta do winget;
    Mac: a pasta do Homebrew), sem precisar reabrir nada.
"""
import glob
import os
import shutil
import sys


def _pastas_ffmpeg():
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        yield os.path.join(local, "Microsoft", "WinGet", "Links")
        yield from sorted(glob.glob(os.path.join(local, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "*", "bin")))
        yield from sorted(glob.glob(os.path.join(local, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "bin")))
        yield os.path.join(os.environ.get("ProgramData", "C:/ProgramData"), "chocolatey", "bin")
        yield "C:/ffmpeg/bin"
    else:
        yield from ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin")


def achar_ffmpeg():
    """Deixa o ffmpeg e o ffprobe no PATH deste processo (e dos que ele abrir). Devolve a pasta, ou None se não achou."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return os.path.dirname(shutil.which("ffmpeg"))
    exe = ".exe" if os.name == "nt" else ""
    for pasta in _pastas_ffmpeg():
        if os.path.isfile(os.path.join(pasta, "ffmpeg" + exe)) and os.path.isfile(os.path.join(pasta, "ffprobe" + exe)):
            os.environ["PATH"] = pasta + os.pathsep + os.environ.get("PATH", "")
            return pasta
    return None


def preparar():
    os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")    # sem os avisos internos do OpenCV que não mudam nada
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if achar_ffmpeg() is None:
        raise SystemExit("[VibeClipper] não achei o ffmpeg. Rode `python instalar.py` pra ver como instalar.")
