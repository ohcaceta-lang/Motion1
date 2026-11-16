"""Tiny procedural audio toolkit: music beds + sound effects, all generated (no third-party samples)."""
import numpy as np, wave, subprocess
from scipy.signal import butter, sosfilt, lfilter, fftconvolve, sawtooth

SR = 48000
rng = np.random.default_rng(11)

class Track:
    def __init__(self, dur): self.n = int(dur * SR); self.buf = np.zeros((2, self.n))
    def add(self, x, t, gain=1.0, pan=0.0):
        x = np.asarray(x, float)
        if x.ndim == 1: x = np.vstack([x * np.sqrt(0.5 * (1 - pan)), x * np.sqrt(0.5 * (1 + pan))]) * np.sqrt(2)
        i = int(t * SR)
        if i >= self.n: return
        if i < 0: x = x[:, -i:]; i = 0
        m = min(x.shape[1], self.n - i); self.buf[:, i:i + m] += x[:, :m] * gain

def secs(d): return np.arange(int(d * SR)) / SR
def lp(x, f, order=2): return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)
def noise(d): return rng.standard_normal(int(d * SR))
def env_ad(n, a, d): u = np.arange(n) / SR; return np.minimum(1, u / max(a, 1e-4)) * np.exp(-u / d)
def norm(x, peak=1.0): m = np.max(np.abs(x)); return x / m * peak if m > 0 else x
def midi(m): return 440 * 2 ** ((m - 69) / 12)

def reverb(x, seconds=2.2, wet=0.3, tone=5000):
    """Stereo convolution reverb from a synthetic decaying-noise impulse response."""
    n = int(seconds * SR); u = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-u * 6.9 / seconds); ir = lp(ir, tone); ir[:int(0.012 * SR)] = 0
        src = x[ch] if x.ndim == 2 else x
        out.append(fftconvolve(src, ir)[:len(src)] * 0.08)
    w = np.vstack(out); dry = x if x.ndim == 2 else np.vstack([x, x])
    return dry * (1 - wet) + norm(w, np.max(np.abs(dry)) + 1e-9) * wet

# ---------------- instruments ----------------
def piano(m, d=3.0, vel=1.0):
    t = secs(d); f = midi(m); y = np.zeros_like(t)
    for h, a in [(1, 1), (2, .45), (3, .22), (4, .12), (5, .06), (6, .04)]:
        fh = f * h * (1 + 0.0004 * h * h)
        y += a * np.sin(2 * np.pi * fh * t) * np.exp(-t * (1.2 + h * 0.9))
    y *= np.minimum(1, t / 0.004)
    y += lp(noise(d), 3000) * np.exp(-t * 60) * 0.05  # hammer
    return y * vel * 0.35

def pluck(m, d=2.5, bright=0.5, decay=0.996):
    """Karplus-Strong string (acoustic guitar-ish)."""
    f = midi(m); N = int(SR / f); n = int(d * SR)
    x = np.zeros(n); burst = lp(rng.uniform(-1, 1, N), 1500 + 6000 * bright); x[:N] = burst
    a = np.zeros(N + 2); a[0] = 1; a[N] = -0.5 * decay; a[N + 1] = -0.5 * decay
    y = lfilter([1], a, x)
    y = hp(y, 70) * np.minimum(1, np.arange(n) / (0.002 * SR))
    return y * 0.5

def strum(notes, t0, track, gain=1.0, down=True, spread=0.018, d=2.6, pan=0.0):
    order = notes if down else notes[::-1]
    for k, m in enumerate(order): track.add(pluck(m, d, bright=0.45 + 0.1 * k / len(notes)), t0 + k * spread, gain * (0.9 if k else 1), pan)

def pad(ms, d, gain=0.15, cutoff=1200, detune=0.006):
    t = secs(d); y = np.zeros_like(t)
    for m in ms:
        for dt in (-detune, 0, detune):
            y += sawtooth(2 * np.pi * midi(m) * (1 + dt) * t + rng.uniform(0, 6))
    y = lp(y, cutoff, 2); e = np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 1.2)
    return y * e * gain / (3 * len(ms))

def drone(m, d, gain=0.2):
    t = secs(d)
    y = sum(sawtooth(2 * np.pi * midi(m + o) * (1 + dt) * t) for o in (0, 12, 7) for dt in (-0.003, 0.003))
    y = lp(y, 380 + 220 * np.sin(2 * np.pi * t / 9) ** 2, 2) if False else lp(y, 520, 3)
    y *= (0.75 + 0.25 * np.sin(2 * np.pi * t / 6.5)) * np.minimum(1, t / 2) * np.minimum(1, (d - t) / 1.5)
    return y * gain / 6

def kick(gain=1.0, soft=False):
    t = secs(0.5); f = 50 + (140 if not soft else 80) * np.exp(-t * 35)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (8 if not soft else 11))
    return y * gain

def heartbeat(gain=1.0):
    a = kick(1, True); b = kick(0.7, True); y = np.zeros(int(0.7 * SR)); y[:len(a)] += a; i = int(0.22 * SR); y[i:i + len(b)] += b[:len(y) - i]
    return lp(y, 180) * gain

def shaker(gain=0.1):
    y = hp(noise(0.09), 6000) * env_ad(int(0.09 * SR), 0.01, 0.025); return y * gain

def hat(gain=0.1):
    return hp(noise(0.06), 8000) * env_ad(int(0.06 * SR), 0.001, 0.015) * gain

def snare_soft(gain=0.3):
    t = secs(0.25); return (bp(noise(0.25), 1200, 6000) * np.exp(-t * 22) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * .5) * gain

# ---------------- sound effects ----------------
def whoosh(d=0.6, gain=0.5, up=True):
    n = int(d * SR); u = np.linspace(0, 1, n); e = np.sin(np.pi * u) ** 2
    x = noise(d); y = np.zeros(n)
    # sweep: blend of bands following envelope
    lo, hi = lp(x, 600), bp(x, 1500, 7000)
    mixc = u if up else 1 - u
    y = lo * (1 - mixc) + hi * mixc * 0.6
    return norm(y * e, gain)

def riser(d=1.5, gain=0.4):
    t = secs(d); u = t / d
    y = bp(noise(d), 300, 9000) * u ** 2.5
    y += sawtooth(2 * np.pi * (200 + 900 * u ** 2) * t) * 0.15 * u ** 2
    return norm(lp(y, 9000), gain) * np.minimum(1, (d - t) / 0.02)

def impact(gain=0.8, low=45):
    t = secs(1.6); f = low + 90 * np.exp(-t * 18)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    y += lp(noise(1.6), 900) * np.exp(-t * 14) * 0.5
    return norm(y, gain)

def typekey(gain=0.25):
    t = secs(0.07); y = bp(noise(0.07), 1800, 7000) * np.exp(-t * 160) + np.sin(2 * np.pi * 120 * t) * np.exp(-t * 90) * 0.6
    return y * gain * rng.uniform(0.7, 1.0)

def typing(track, t0, n, cps=14, gain=0.25):
    t = t0
    for _ in range(n): track.add(typekey(gain), t, 1, rng.uniform(-.3, .3)); t += 1 / cps * rng.uniform(0.7, 1.3)

def bell(f=2100, gain=0.25, d=1.5):
    t = secs(d); y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * (3 + 2 * k)) for k, (r, a) in enumerate([(1, 1), (2.76, .4), (5.4, .2)]))
    return y * gain

def stamp(gain=0.7):
    t = secs(0.5); y = lp(noise(0.5), 400) * np.exp(-t * 40) + np.sin(2 * np.pi * 70 * t) * np.exp(-t * 25)
    return norm(y, gain)

def paper(d=0.45, gain=0.3):
    n = int(d * SR); e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    y = bp(noise(d), 2000, 9000) * e * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 40, n))))
    return norm(y, gain)

def tick(gain=0.25):
    t = secs(0.04); return bp(noise(0.04), 3000, 9000) * np.exp(-t * 300) * gain + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200) * gain * 0.5

def clang(gain=0.5):
    t = secs(2.0); y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for f, a, dcy in [(220, 1, 2), (517, .7, 3), (1033, .5, 4), (1789, .3, 6), (2671, .2, 8)])
    y += lp(noise(2.0), 2000) * np.exp(-t * 30)
    return norm(y, gain)

def glitch(d=0.35, gain=0.35):
    n = int(d * SR); y = np.zeros(n); i = 0
    while i < n:
        L = int(rng.uniform(0.01, 0.05) * SR); f = rng.uniform(80, 1800)
        seg = np.sign(np.sin(2 * np.pi * f * np.arange(L) / SR)) if rng.random() < .5 else rng.uniform(-1, 1, L)
        y[i:i + L] = seg[:n - i] * rng.uniform(.3, 1); i += L
    return lp(y, 7000) * gain

def popfx(gain=0.35, f0=500):
    t = secs(0.12); f = f0 + 900 * np.exp(-t * 60); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * gain

def pin_drop(gain=0.5):
    a = pluck(76, 1.2, 0.8); b = lp(kick(0.6, True), 300); a[:len(b)] += b
    return norm(a, gain)

def kaching(gain=0.45):
    y = np.zeros(int(1.6 * SR))
    b1, b2 = bell(2637, 1, 1.4), bell(3520, 0.8, 1.2); y[:len(b1)] += b1; i = int(0.09 * SR); y[i:i + len(b2)] += b2[:len(y) - i]
    c = bp(noise(0.15), 3000, 9000) * np.exp(-secs(0.15) * 40); y[:len(c)] += c * 0.6
    return norm(y, gain)

def bird(gain=0.12):
    d = rng.uniform(0.08, 0.16); t = secs(d); f0 = rng.uniform(2800, 4200)
    f = f0 + rng.uniform(600, 1500) * np.sin(np.pi * t / d) * rng.choice([-1, 1])
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
    return y * gain

def birds(track, t0, t1, rate=2.2, gain=0.1):
    t = t0
    while t < t1:
        k = rng.integers(2, 5)
        for j in range(k): track.add(bird(gain), t + j * 0.13, 1, rng.uniform(-.8, .8))
        t += rng.exponential(1 / rate) + 0.3

def city(d, gain=0.25):
    t = secs(d)
    y = lp(noise(d), 350, 2) * (0.8 + 0.2 * np.sin(2 * np.pi * t / 3.1)) + bp(noise(d), 800, 2500) * 0.08
    return norm(y, gain)

def scratch(d=1.2, gain=0.2):
    n = int(d * SR); u = np.arange(n) / SR
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * u)) * np.abs(np.sin(2 * np.pi * 3.3 * u))
    return norm(bp(noise(d), 2500, 8000) * am * np.minimum(1, (d - u) / 0.05), gain)

def chime(gain=0.25):
    y = np.zeros(int(3 * SR))
    for k, m in enumerate([84, 88, 91, 96]):
        b = bell(midi(m), 1, 2.4); i = int(k * 0.07 * SR); y[i:i + len(b)] += b[:len(y) - i]
    return norm(y, gain)

# ---------------- output ----------------
def sidechain(music, fx_times, depth=0.35, rel=0.35):
    """Duck the music briefly under hits (keeps impacts readable)."""
    g = np.ones(music.shape[1])
    for t in fx_times:
        i = int(t * SR); n = int(rel * SR); u = np.linspace(0, 1, n)
        seg = 1 - depth * (1 - u) ** 2; g[i:i + n] = np.minimum(g[i:i + n], seg[:max(0, min(n, len(g) - i))])
    return music * g

def write(path, stereo, peak=0.89):
    y = stereo / max(1e-9, np.max(np.abs(stereo))) * peak
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y.T * 32767).astype(np.int16).tobytes())
