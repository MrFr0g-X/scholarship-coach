"""Deterministic frame-by-frame renderer for index.html (GSAP timeline -> MP4).

python render.py stills 2.6 6.5 12 ...     # PNG stills for review
python render.py video out.mp4 [--fps 60]  # full render, piped to ffmpeg
"""
import os
import subprocess
import sys
import time

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = sys.argv[sys.argv.index("--page") + 1] if "--page" in sys.argv else "index.html"
URL = "file:///" + os.path.join(HERE, PAGE).replace("\\", "/")
FF = imageio_ffmpeg.get_ffmpeg_exe()


def open_page(p):
    b = p.chromium.launch(args=["--force-color-profile=srgb", "--disable-gpu-vsync"])
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("window.__ready")
    pg.wait_for_timeout(300)
    return b, pg, errs


def stills(times):
    os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
    with sync_playwright() as p:
        b, pg, errs = open_page(p)
        print("duration", pg.evaluate("window.__DUR"))
        for t in times:
            pg.evaluate(f"window.__seek({t})")
            out = os.path.join(HERE, "stills", f"t{float(t):05.2f}.png")
            pg.screenshot(path=out)
            print(out)
        if errs:
            print("CONSOLE:", *errs[:10], sep="\n  ")
        b.close()


def video(out, fps=60):
    with sync_playwright() as p:
        b, pg, errs = open_page(p)
        dur = pg.evaluate("window.__DUR")
        n = int(round(dur * fps))
        cmd = [FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
               "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", out]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        t0 = time.time()
        for i in range(n):
            pg.evaluate(f"window.__seek({i / fps})")
            ff.stdin.write(  # type: ignore[union-attr]
                pg.screenshot(type="jpeg", quality=96))
            if i % 300 == 0:
                print(f"frame {i}/{n}  {time.time() - t0:.0f}s", flush=True)
        ff.stdin.close()  # type: ignore[union-attr]
        ff.wait()
        if errs:
            print("CONSOLE:", *errs[:10], sep="\n  ")
        b.close()
        print("done", out, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills([float(x) for x in sys.argv[2:] if x.replace(".", "").isdigit()])
    else:
        fps = int(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 60
        video(sys.argv[2], fps)
