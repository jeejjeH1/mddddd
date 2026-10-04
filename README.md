# PrismaX × IROS 2026 — motion graphic

A 40-second, 1920×1080 brand motion piece built from the IROS 2026 Pittsburgh photos.

**Final video:** [`out/prismax-iros2026.mp4`](out/prismax-iros2026.mp4) (H.264 + AAC, 30 fps, with an original beat-synced soundtrack)

## Storyboard (120 BPM, cuts on the bar)

| Time | Scene | Content |
|---|---|---|
| 0–4s | Intro | Bronze slats (booth-wall motif), Prisma(x) wordmark, "The service layer for physical AI" |
| 4–8s | 01 Tech Talk Stage | Schedule photo, highlight frame on the 3:15 PM PrismaX slot, push-in zoom |
| 8–14s | 02 The Talk | Split-screen stage photo and "What makes good robotics data?", key finding |
| 14–20s | 03 The Booth | Teleop rig with perception-style detection boxes, booth conversation |
| 20–26s | 04 What we do | Cream "flyer" palette: teleoperated manipulation, egocentric capture, customizable data |
| 26–32s | 05 By the numbers | 5,000 hrs/month · 1,700+ scenarios · 120K+ episodes · backed by a16z, NVIDIA, MIT, Stanford |
| 32–36s | Let there be robots. | Kinetic type slams, tote bag and keychains |
| 36–40s | Outro | Wordmark, tagline, prismax.ai |

## Brand kit used
prismax.ai was not reachable from the build environment, so the kit was taken from the booth, flyer and merch photos:

- **Colours:** ink `#0e0a08`, espresso `#15100c` / `#3a2a20`, bronze ramp `#6f472e → #ecd0a6`, paper cream `#f2ede4`, rust accent `#a3432b`
- **Type:** Instrument Serif (wordmark, headlines), Inter Tight (slogan, body), JetBrains Mono (labels)
- **Wordmark:** recreated as `Pr\sma(x)` in type. For final delivery, swap in the official logo file.

## Edit and re-render
```bash
cd scripts && npm install && cd ..
python3 scripts/make_audio.py          # -> out/soundtrack.wav (needs numpy)
node scripts/render.mjs                # -> out/prismax-iros2026.mp4
node scripts/render.mjs --stills 5,20  # quick PNG checks
node scripts/render.mjs --fps 60       # smoother master
```
Open `index.html` via any static server (`npx serve .`) to scrub and preview in the browser with sound.
