# Showreel source

The video in the main README is code. `index.html` is one GSAP timeline. `render.py` opens it in headless Chromium, seeks the timeline one frame at a time and pipes the frames into ffmpeg. `soundtrack.py` generates the music and sound effects, so nothing is licensed from anyone.

```bash
npm install                     # gsap
pip install playwright imageio-ffmpeg numpy pillow
python -m playwright install chromium

python render.py stills 2.9 18.2 45.9    # check single frames
python render.py video showreel_raw.mp4  # full 1080p60 render, about 3 minutes
python soundtrack.py                     # soundtrack.wav
python gif.py                            # demo.gif for the README
python render.py video pipeline_raw.mp4 --page pipeline.html
python gif.py pipeline.html pipeline.gif # the How it works animation
```

Mux sound and picture:

```bash
ffmpeg -i showreel_raw.mp4 -i soundtrack.wav -c:v copy -c:a aac -b:a 192k -shortest showreel.mp4
```
