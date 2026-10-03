"""Procedural, license-free soundtrack synced to the showreel timeline."""
import wave

import numpy as np

SR = 48000
DUR = 47.2
N = int(SR * DUR)
rng = np.random.default_rng(7)
out = np.zeros((N, 2))
t_all = np.arange(N) / SR


def env(n, a, r):
    e = np.ones(n)
    a, r = int(a * SR), int(r * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    out[i:i + len(sig), 0] += sig * gain * l * 1.414
    out[i:i + len(sig), 1] += sig * gain * r * 1.414


def lowpass(x, cut):
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def note(f):
    return 440 * 2 ** ((f - 69) / 12)


# --- pad: Am  F  C  G (2 bars each at 120bpm = 4s per chord) ---
chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
for k, at in enumerate(np.arange(0, 46, 4.0)):
    ch = chords[k % 4]
    n = int(4.6 * SR)
    tt = np.arange(n) / SR
    sig = np.zeros(n)
    for m in ch:
        f = note(m)
        sig += 0.5 * np.sin(2 * np.pi * f * tt) + 0.18 * np.sin(2 * np.pi * f * 2.003 * tt) + 0.08 * np.sin(2 * np.pi * f * 0.5 * tt)
    sig *= env(n, 1.2, 1.4) / len(ch)
    add(sig, at, 0.22, pan=-0.2 if k % 2 else 0.2)

# sub bass on chord roots
for k, at in enumerate(np.arange(4.0, 46, 4.0)):
    root = chords[k % 4][0] - 12
    n = int(3.9 * SR)
    tt = np.arange(n) / SR
    add(np.sin(2 * np.pi * note(root) * tt) * env(n, .05, 1.0), at, 0.16)

# --- drums (off during intro and night scene) ---
def kick():
    n = int(.35 * SR); tt = np.arange(n) / SR
    f = 110 * np.exp(-tt * 22) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)


def hat():
    n = int(.06 * SR)
    x = rng.standard_normal(n)
    x = x - lowpass(x, 6000)
    return x * np.exp(-np.arange(n) / SR * 70)


beat = 0.5
for b in np.arange(4.2, 45.0, beat):
    if 21.2 <= b < 27.2 or 42.0 <= b:
        continue
    add(kick(), b, 0.55)
    add(hat(), b + beat / 2, 0.10, pan=0.4)

# --- whoosh on every cut ---
def whoosh(d=.55):
    n = int(d * SR)
    x = rng.standard_normal(n)
    sw = np.linspace(400, 5000, n)
    y = np.zeros(n); acc = 0.0
    for i in range(n):
        a = np.exp(-2 * np.pi * sw[i] / SR)
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y * np.sin(np.linspace(0, np.pi, n)) ** 2


for c in [4.2, 10.2, 15.2, 21.0, 27.0, 33.2, 38.6, 42.4]:
    add(whoosh(), c - 0.3, 0.55)

# --- typing clicks ---
def click():
    n = int(.018 * SR)
    x = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 400)
    return x - lowpass(x, 1500)


for a, b, cnt in [(0.35, 1.35, 17), (1.5, 2.3, 13), (39.0, 40.1, 18), (40.3, 40.85, 9), (41.0, 41.6, 10)]:
    for ti in np.linspace(a, b, cnt):
        add(click(), ti + rng.uniform(-.01, .01), 0.18, pan=rng.uniform(-.3, .3))

# --- impacts ---
def impact():
    n = int(1.2 * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * (60 * np.exp(-tt * 3) + 35) * tt) * np.exp(-tt * 3.5)
    nz = rng.standard_normal(n) * np.exp(-tt * 18) * .3
    return body + nz


add(impact(), 8.85, 0.7)
add(impact(), 17.5, 0.45)
add(impact(), 25.25, 0.5)

# --- chimes (check marks) ---
def chime(f):
    n = int(1.6 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 3)


add(chime(note(76)), 19.0, 0.18)
add(chime(note(79)), 41.0, 0.16)
add(chime(note(81)), 43.4, 0.22)
add(chime(note(88)), 43.55, 0.12)

# --- riser into the end card ---
n = int(1.2 * SR); tt = np.arange(n) / SR
add(np.sin(2 * np.pi * np.cumsum(200 + 1400 * (tt / tt[-1]) ** 2) / SR) * (tt / tt[-1]) ** 2 * .5, 41.2, 0.25)

# master: gentle fade in/out, soft clip, normalize
fade = np.ones(N)
fade[: int(.4 * SR)] = np.linspace(0, 1, int(.4 * SR))
fi = int(45.2 * SR)
fade[fi:] = np.linspace(1, 0, N - fi)
out *= fade[:, None]
out = np.tanh(out * 1.2)
out /= np.max(np.abs(out)) / 0.89

pcm = (out * 32767).astype(np.int16)
with wave.open("soundtrack.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("soundtrack.wav", DUR, "s  rms", float(np.sqrt(np.mean(out ** 2))))
