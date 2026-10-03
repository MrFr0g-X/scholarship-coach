"""Render GIF-friendly highlight frames (no grain) and assemble demo.gif."""
import io, os, subprocess
import imageio_ffmpeg
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
PAGE = sys.argv[1] if len(sys.argv) > 1 else "index.html"
OUT = sys.argv[2] if len(sys.argv) > 2 else "demo.gif"
URL = "file:///" + os.path.join(HERE, PAGE).replace("\\", "/") + "?nograin"
SEGS = [(1.0, 2.9), (6.0, 9.6), (11.6, 13.6), (16.3, 18.2), (25.2, 26.4), (29.0, 31.2), (43.0, 45.8)] if PAGE == "index.html" else [(4.2, 15.2), (0.0, 4.2)]
FPS = 15
FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs("gifframes", exist_ok=True)
for f in os.listdir("gifframes"):
    os.remove(os.path.join("gifframes", f))
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto(URL, wait_until="networkidle"); pg.evaluate("window.__ready"); pg.wait_for_timeout(300)
    k = 0
    for a, z in SEGS:
        # step forward from segment start so timeline callbacks fire in order
        pg.evaluate(f"window.__seek({max(0, a - 0.5)})")
        t = a
        while t < z:
            pg.evaluate(f"window.__seek({t})")
            pg.screenshot(path=f"gifframes/f{k:04d}.png")
            k += 1; t += 1 / FPS
    b.close()
fc = "fps=15,scale=900:-1:flags=lanczos,split[x][y];[x]palettegen=max_colors=96:stats_mode=full[p];[y][p]paletteuse=dither=bayer:bayer_scale=4"
subprocess.run([FF, "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", "gifframes/f%04d.png", "-filter_complex", fc, "-loop", "0", OUT], check=True)
print("frames", k, "size MB", round(os.path.getsize(OUT) / 1e6, 2))
