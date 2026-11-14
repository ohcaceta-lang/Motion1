"""Shorten long pauses in a voiceover using its word timings, speed it up, and output new word timings.
usage: python3 tighten.py voice.mp3 words.txt out_prefix [tempo]"""
import sys, json, subprocess, numpy as np, wave
src, wfile, out = sys.argv[1:4]; tempo = float(sys.argv[4]) if len(sys.argv) > 4 else 1.1
SR = 48000
W = [(a, float(b), float(c)) for a, b, c in (x.split(' ') for x in open(wfile).read().strip().split('|'))]
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(float) / 32768
cuts = []  # (start, end) removed
for (w, s, e), (_, s2, _) in zip(W, W[1:]):
    cap = 0.45 if w[-1] in '.?!:' or w.endswith('...') else (0.32 if w[-1] == ',' else 0.16)
    gap = s2 - e
    if gap > cap: cuts.append((e + cap * 0.5, s2 - cap * 0.5))
lead = max(0, W[0][1] - 0.05); cuts.insert(0, (0, lead))
cuts.append((W[-1][2] + 0.35, len(x) / SR))
def remap(t): return t - sum(min(b, max(a, t)) - a for a, b in cuts)
fade = int(0.012 * SR); keep = []; prev = 0
for a, b in cuts:
    ia, ib = int(a * SR), int(b * SR)
    if ia > prev: keep.append(x[prev:ia])
    prev = max(prev, ib)
if prev < len(x): keep.append(x[prev:])
y = keep[0]
for seg in keep[1:]:
    if len(seg) > fade and len(y) > fade:
        r = np.linspace(0, 1, fade); y = np.concatenate([y[:-fade], y[-fade:] * (1 - r) + seg[:fade] * r, seg[fade:]])
    else: y = np.concatenate([y, seg])
with wave.open(out + '_tmp.wav', 'wb') as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', out + '_tmp.wav', '-af', f'atempo={tempo}', out + '.wav'], check=True)
words = [{'w': w, 's': round(remap(s) / tempo, 3), 'e': round(remap(e) / tempo, 3)} for w, s, e in W]
json.dump(words, open(out + '.json', 'w'), ensure_ascii=False)
d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out + '.wav']))
print(out, 'duration', round(d, 2), 'words', len(words))
