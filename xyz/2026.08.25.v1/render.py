"""Renders the description card from the HTML source rather than from a screenshot.

The card, its corners and its shadow are drawn by the browser at device scale 3, so the corners are
antialiased and the text is vector sharp. The light variant remaps the palette's pale shades to dark
ones, since the authored ramps are tuned for a dark background and wash out on white.
"""

import os, re, subprocess, sys
from PIL import Image

ROOT   = "/Volumes/m/projects/si.intellij.plugin.Spaceflow.Gradled"
SOURCE = f"{ROOT}/src/momomo/intellij/Core/descriptions/description.about.plugin.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HERE   = os.path.dirname(os.path.abspath(__file__))
OUT    = sys.argv[1]

PAGE_W   = 900          # The width the statics are cut to
GUTTER   = 16           # Room for the shadow, inside PAGE_W
PAD      = 26           # The mat
CONTENT  = PAGE_W - GUTTER * 2 - PAD * 2
ZOOM     = 1                                # The fragment is authored at 600px, left there
DSF      = 3            # Supersample, then come back down

fragment = open(SOURCE).read()

# The dark ramps are pale by design. On white the top half of each is unreadable, so it is remapped.
LIGHT_REMAP = """
    .o,.o1,.o2,.o3,.o4,.o5,.o6,.o7,.o8,.o9 { color:#B4560A !important; }
    .a,.a1,.a2,.a3,.a4,.a5,.a6,.a7,.a8,.a9 { color:#9A6A08 !important; }
    .r,.r1,.r2,.r3,.r4,.r5,.r6,.r7,.r8,.r9 { color:#C63512 !important; }
    .g,.g1,.g2,.g3,.g4,.g5,.g6,.g7,.g8,.g9 { color:#0A7A4A !important; }
    .b,.b1,.b2,.b3,.b4,.b5,.b6,.b7,.b8,.b9 { color:#1A5FBF !important; }
    .v,.v1,.v2,.v3,.v4,.v5,.v6,.v7,.v8,.v9 { color:#7A2AC4 !important; }
"""

SHELL = """<!doctype html><html><head><meta charset="utf-8"><style>
  html, body {{ margin:0; padding:0; background:transparent; width:{page}px; }}
  .gutter {{ padding:{gutter}px; }}
  .card {{
      width:{card}px; padding:{pad}px; box-sizing:border-box;
      border-radius:{radius}px; background:{bg}; color:{fg};
      font-family:-apple-system,"SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
      box-shadow:{shadow};
      {border}
  }}
  .card {{ font-size:17px; line-height:1.62; }}
  .card .zoom > div {{ width:auto !important; }}   /* The fragment is authored at 600px, let it fill */
  .card img {{ max-width:100%; }}
  {extra}
</style></head><body>
  <div class="gutter"><div class="card"><div class="zoom">{fragment}</div></div></div>
</body></html>"""


def render(name, bg, fg, shadow, border, extra):
    page = os.path.join(HERE, f"page.{name}.html")
    with open(page, "w") as f:
        f.write(SHELL.format(page=PAGE_W, gutter=GUTTER, card=PAGE_W - GUTTER * 2, pad=PAD,
                             radius=20, bg=bg, fg=fg, shadow=shadow, border=border,
                             zoom=round(ZOOM, 4), extra=extra, fragment=fragment))

    raw = os.path.join(OUT, f".raw.{name}.png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                    f"--force-device-scale-factor={DSF}", f"--window-size={PAGE_W},5200",
                    "--default-background-color=00000000", "--virtual-time-budget=4000",
                    f"--screenshot={raw}", f"file://{page}"], capture_output=True)

    im  = Image.open(raw).convert("RGBA")
    box = im.getbbox()                                   # Trims the transparent page around the card
    if box is None:
        raise SystemExit(f"{name}: nothing rendered")
    if box[3] >= im.height - 4:
        raise SystemExit(f"{name}: content reached the bottom of the window, raise the height")

    im = im.crop((0, 0, PAGE_W * DSF, box[3] + 1))       # Full width, exact height, nothing cropped
    os.remove(raw)

    for width in (PAGE_W * 2, PAGE_W):
        out = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        out.save(os.path.join(OUT, f"{name}.{width}.png"), optimize=True)
        print(f"{name}.{width}.png".ljust(30), f"{out.width}x{out.height}")


os.makedirs(OUT, exist_ok=True)

render("description.dark", bg="#202224", fg="#D7D8DC",
       shadow="0 2px 6px rgba(0,0,0,.28), 0 10px 26px rgba(0,0,0,.30), 0 22px 48px rgba(0,0,0,.26)",
       border="border:1px solid rgba(255,255,255,.09);",
       extra=".card { background:linear-gradient(180deg,#232527 0%,#202224 12%,#202224 88%,#1D1F21 100%); }")

render("description.light", bg="#FFFFFF", fg="#24262E",
       shadow="none", border="", extra=LIGHT_REMAP)
