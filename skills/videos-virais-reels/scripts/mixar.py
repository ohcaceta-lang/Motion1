"""Mixagem final: narração + música (em loop, abaixando sob a voz) + efeitos sonoros sintetizados,
e (opcional) junta com o vídeo mudo normalizando para -14 LUFS (padrão Reels/TikTok).

uso:
  python3 mixar.py --voz voz.wav --musica musica.mp3 --dur 31.6 --cues cues.json --out mix.wav \
                   [--video mudo.mp4 --final Video_Final.mp4] [--musica-vol 0.32]

cues.json = lista de marcações. Cada item tem "fx" e "t" (segundos), e opcionalmente "g" (ganho) e "pan".
  Efeitos pontuais (fx):  whoosh, impact, stamp, paper, clang, glitch, pop, pin_drop, kaching, chime,
                          bell, riser, tick, scratch, typekey
  Efeitos com intervalo:  {"fx":"typing","t":6.2,"n":7,"cps":16}
                          {"fx":"ticks","t":0.2,"t1":6.0,"n":12}        (relógio / contador)
                          {"fx":"birds","t":2.9,"t1":16.5}
                          {"fx":"crickets","t":29,"t1":35.8}
                          {"fx":"city","t":0,"t1":2.9}                 (trânsito ao fundo)
                          {"fx":"muffle","t":0,"t1":2.8}               (abafa a música nesse trecho)
"""
import argparse, json, subprocess, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import *

ap = argparse.ArgumentParser()
ap.add_argument('--voz', required=True); ap.add_argument('--musica', required=True)
ap.add_argument('--dur', type=float, required=True); ap.add_argument('--cues', required=True)
ap.add_argument('--out', default='mix.wav'); ap.add_argument('--video'); ap.add_argument('--final')
ap.add_argument('--musica-vol', type=float, default=0.32)
a = ap.parse_args()
DUR = a.dur

def load(path):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return (np.frombuffer(raw, np.int16).astype(float) / 32768).reshape(-1, 2).T

voice, music = load(a.voz), load(a.musica)
n = int(DUR * SR)
# música em loop com crossfade de 2,5 s até cobrir o vídeo
xf = int(2.5 * SR); bed = music.copy()
while bed.shape[1] < n:
    r = np.linspace(0, 1, xf); c, s_ = np.cos(r * np.pi / 2), np.sin(r * np.pi / 2)
    bed = np.concatenate([bed[:, :-xf], bed[:, -xf:] * c + music[:, :xf] * s_, music[:, xf:]], axis=1)
bed = bed[:, :n]
# ducking sob a voz
env = np.zeros(n); v = np.abs(voice).mean(0); m = min(len(v), n); env[:m] = v[:m]
env = lp(env, 3); nz = env[env > 0]
env = np.clip(env / (np.percentile(nz, 90) + 1e-9), 0, 1) if len(nz) else env
bed = bed * (1 - 0.5 * env) * a.musica_vol
u = np.arange(n) / SR; bed *= np.clip(u / 0.6, 0, 1) * np.clip((DUR - u) / 1.5, 0, 1)

ONE = {'whoosh': lambda g: whoosh(0.6, 0.45 * g), 'impact': lambda g: impact(0.7 * g), 'stamp': lambda g: stamp(0.8 * g),
       'paper': lambda g: paper(0.45, 0.32 * g), 'clang': lambda g: clang(0.55 * g), 'glitch': lambda g: glitch(0.35, 0.33 * g),
       'pop': lambda g: popfx(0.33 * g), 'pin_drop': lambda g: pin_drop(0.55 * g), 'kaching': lambda g: kaching(0.5 * g),
       'chime': lambda g: chime(0.22 * g), 'bell': lambda g: bell(2100, 0.2 * g), 'riser': lambda g: riser(1.6, 0.35 * g),
       'tick': lambda g: tick(0.25 * g), 'scratch': lambda g: scratch(1.0, 0.1 * g), 'typekey': lambda g: typekey(0.3 * g)}
T = Track(DUR); hits = []
for c in json.load(open(a.cues)):
    fx, t, g, pan = c['fx'], float(c['t']), float(c.get('g', 1)), float(c.get('pan', 0))
    t1 = float(c.get('t1', t))
    if fx in ONE:
        x = ONE[fx](g); T.add(x, t - (0.36 if fx == 'whoosh' else 1.55 if fx == 'riser' else 0), 1, pan)
        if fx in ('whoosh', 'impact', 'stamp', 'clang', 'kaching', 'pin_drop'): hits.append(t)
    elif fx == 'typing': typing(T, t, int(c.get('n', 6)), float(c.get('cps', 14)), 0.3 * g)
    elif fx == 'ticks':
        k = int(c.get('n', 10))
        for i in range(k): T.add(tick(0.22 * g), t + i * (t1 - t) / max(k, 1))
    elif fx == 'birds': birds(T, t, t1, float(c.get('rate', 1.3)), 0.07 * g)
    elif fx == 'crickets':
        tt = t
        while tt < t1:
            for j in range(3): T.add(np.sin(2 * np.pi * 4600 * secs(0.03)) * np.hanning(int(0.03 * SR)) * 0.04 * g, tt + j * 0.05, 1, 0.5)
            tt += 0.62
    elif fx == 'city':
        d = t1 - t; x = city(d, 0.35 * g); T.add(x * np.minimum(1, (d - np.arange(len(x)) / SR) / 0.4), t)
    elif fx == 'muffle':
        i0, i1 = int(t * SR), int(t1 * SR); bed[:, i0:i1] = np.vstack([lp(bed[0, i0:i1], 500), lp(bed[1, i0:i1], 500)]) * 0.8
    else:
        print('efeito desconhecido:', fx, file=sys.stderr)
sfx = reverb(T.buf, 1.4, 0.18)
bed = sidechain(bed, hits, 0.4, 0.35)
vt = Track(DUR); vt.add(voice, 0.0)
write(a.out, vt.buf + bed + sfx * 0.55)
print('mix ok', a.out, DUR, 's')
if a.video and a.final:
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', a.video, '-i', a.out, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest',
                    '-movflags', '+faststart', a.final], check=True)
    print('final ok', a.final)
