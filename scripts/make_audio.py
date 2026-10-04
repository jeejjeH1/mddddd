"""Synthesises the 40s soundtrack, beat-locked to the timeline in index.html.

120 BPM, one bar = 2s. Scene cuts (impacts) land on 4, 8, 14, 20, 26, 32, 36.
Writes out/soundtrack.wav (48 kHz, 16-bit stereo).
"""
import wave
from pathlib import Path

import numpy as np

SR = 48000
DUR = 40.0
N = int(SR * DUR)
BEAT = 0.5
CUTS = [4, 8, 14, 20, 26, 32, 36]
rng = np.random.default_rng(3)
L = np.zeros(N)
R = np.zeros(N)


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gain * l * 1.414
    R[i:i + len(sig)] += sig * gain * r * 1.414


def tt(d):
    return np.arange(int(d * SR)) / SR


def hz(note):  # midi -> Hz
    return 440.0 * 2 ** ((note - 69) / 12)


def onepole(x, a):  # simple lowpass, a in (0,1) (scalar or per-sample): smaller = darker
    a = np.broadcast_to(np.asarray(a, dtype=float), x.shape)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


# ---------- instruments ----------
def kick():
    t = tt(0.45)
    f = 45 + 95 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.25
    return (np.sin(ph) * np.exp(-t * 7.5) + click) * 0.9


def hat(dec=55):
    t = tt(0.09)
    n = rng.standard_normal(len(t))
    n = np.diff(n, prepend=0)  # crude high-pass
    return n * np.exp(-t * dec) * 0.18


def clap():
    t = tt(0.35)
    n = rng.standard_normal(len(t))
    n = n - onepole(n, 0.08)
    env = np.zeros(len(t))
    for k, o in enumerate((0, 0.011, 0.022)):
        i = int(o * SR)
        env[i:] += np.exp(-(t[: len(t) - i]) * (90 if k < 2 else 16))
    return n * env * 0.35


def impact(big=1.0):
    t = tt(2.2)
    f = 32 + 38 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    n = rng.standard_normal(len(t))
    hiss = onepole(n, 0.25) * np.exp(-t * 7) * 0.55
    return (boom + hiss) * big


def riser(d=1.0):
    t = tt(d)
    n = rng.standard_normal(len(t))
    shaped = n - onepole(n, 0.04 + 0.5 * (t / d) ** 2)  # opens up as it rises
    sweep = np.sin(2 * np.pi * np.cumsum(300 + 1500 * (t / d) ** 2) / SR) * 0.08
    return (shaped * 0.5 + sweep) * (t / d) ** 2.4


def blip(f=1900, d=0.07):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * 0.22


def pluck(f, d=0.28):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 14) * 0.16


def pad_note(f, d):
    t = tt(d)
    s = np.zeros(len(t))
    for det in (-0.12, 0.0, 0.13):  # three detuned voices, soft harmonic stack
        ff = f * 2 ** (det / 12)
        for h in range(1, 7):
            s += np.sin(2 * np.pi * ff * h * t + h) / h ** 1.6
    a = np.minimum(1, t / 0.35)
    r = np.minimum(1, (d - t) / 0.5)
    return s * a * np.clip(r, 0, 1) * 0.045


# ---------- arrangement ----------
# A minor: Am – F – C – G per bar
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
ROOTS = [45, 41, 36, 43]
bars = int(DUR / 2)

for b in range(bars):
    at = b * 2
    ch = CHORDS[b % 4]
    if at >= 38:
        break
    d = 2.6 if at < 36 else 4.0
    if at == 36:
        ch = CHORDS[0]
    for k, n in enumerate(ch):
        add(pad_note(hz(n), d), at, 1.0 if not (32 <= at < 36) else 0.7, pan=(k - 1) * 0.5)
    # sub bass from the first cut
    if 4 <= at < 32 or at >= 36:
        t = tt(2.0 if at < 36 else 4.0)
        sub = np.sin(2 * np.pi * hz(ROOTS[b % 4] - 12 + 12) * t) * 0.32
        sub *= np.minimum(1, t / 0.02) * np.clip((t[-1] - t) / 0.1, 0, 1)
        add(sub, at)

# sidechain duck envelope (for pad/sub) applied later
duck = np.ones(N)

beats = np.arange(0, DUR, BEAT)
for bt in beats:
    bar_pos = round((bt % 2) / BEAT)  # 0..3 within the bar
    if 4 <= bt < 32:
        half = 20 <= bt < 26
        if not half or bar_pos in (0, 2):
            add(kick(), bt, 1.0)
            i = int(bt * SR)
            seg = np.minimum(1, 0.35 + 0.65 * (tt(0.32) / 0.32) ** 0.6)
            duck[i:i + len(seg)] = np.minimum(duck[i:i + len(seg)], seg)
    if 8 <= bt < 32:
        add(hat(), bt + BEAT / 2, 1.0, pan=0.35)
        if 26 <= bt < 32:  # 16ths for the numbers section
            add(hat(80), bt + BEAT / 4, 0.55, pan=-0.35)
            add(hat(80), bt + 3 * BEAT / 4, 0.55, pan=-0.35)
    if 14 <= bt < 32 and bar_pos in (1, 3):
        add(clap(), bt, 1.0)

# arpeggio through pillars + numbers
for i, st in enumerate(np.arange(20, 32, BEAT / 2)):
    b = int(st // 2)
    ch = CHORDS[b % 4]
    note = ch[i % 3] + 12 + (12 if i % 6 >= 3 else 0)
    add(pluck(hz(note)), st, 1.0, pan=-0.4 if i % 2 else 0.4)

# intro shimmer
for k, n in enumerate([76, 79, 84, 88]):
    t = tt(3.6)
    s = np.sin(2 * np.pi * hz(n) * t) * np.minimum(1, t / 0.8) * np.exp(-t * 0.6) * 0.035
    add(s, 0.3 + k * 0.12, pan=(-0.6, 0.6, -0.3, 0.3)[k])

# transitions: riser into each cut, impact on it
for c in CUTS:
    add(riser(1.0 if c != 32 else 0.6), c - (1.0 if c != 32 else 0.6), 0.55, 0.0)
    add(impact(1.0 if c in (4, 36) else 0.7), c, 0.9)
add(impact(0.5), 0.35, 0.6)

# slams on "Let / there / be / robots."
for k, st in enumerate([32, 32.5, 33, 33.5]):
    add(kick(), st, 1.1)
    add(clap(), st, 1.2 if k == 3 else 0.8)
    add(impact(0.5 + 0.15 * k), st, 0.6)
add(kick(), 34, 0.9); add(kick(), 34.5, 0.6); add(kick(), 35, 0.9); add(kick(), 35.5, 0.6)

# UI sound design
for i in range(6):  # detection boxes
    add(blip(1700 + i * 140), 15.5 + i * 0.16 + 0.05, 1.0, pan=-0.3 + i * 0.12)
for i in range(16):  # typewriter on "LIVE FROM IROS"
    add(blip(3200, 0.02), 2.0 + i * 0.056, 0.35, pan=0.2)
for i in range(3):  # counters
    add(blip(1200 + 300 * i, 0.12), 26.35 + i * 0.4, 1.0)
for i in range(4):  # backers
    add(blip(2400, 0.05), 29.0 + 0.12 * (i + 1), 0.6)
add(blip(1500, 0.15), 5.25, 1.0)  # highlight frame
add(blip(2000, 0.1), 37.8, 0.8)  # url underline

# ---------- mix ----------
# duck the sustained layers under the kick: approximate by ducking everything a touch
L *= 0.75 + 0.25 * duck
R *= 0.75 + 0.25 * duck

# small room reverb via FFT convolution
ir_t = tt(1.1)
ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 5.5)
ir2 = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 5.5)
ir[: int(0.012 * SR)] = 0
ir2[: int(0.017 * SR)] = 0


def conv(x, h):
    n = len(x) + len(h)
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[: len(x)]


wl, wr = conv(L, ir), conv(R, ir2)
wl /= np.max(np.abs(wl)) + 1e-9
wr /= np.max(np.abs(wr)) + 1e-9
pk = max(np.max(np.abs(L)), np.max(np.abs(R)))
L = L / pk + wl * 0.12
R = R / pk + wr * 0.12

# fades
t = np.arange(N) / SR
fade = np.clip(t / 0.05, 0, 1) * np.clip((DUR - t) / 2.2, 0, 1)
L *= fade
R *= fade

# glue + limit
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.6) / np.tanh(1.6)
mix *= 0.89 / np.max(np.abs(mix))

out = Path(__file__).resolve().parent.parent / 'out' / 'soundtrack.wav'
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', out)
