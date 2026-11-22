# -*- coding: utf-8 -*-
"""Export images of the cast declared in cast.py (same folder).

    python3 drawkit/export.py              # check + export everything into ../out
    python3 drawkit/export.py --no-png     # SVG only
    python3 drawkit/export.py --out DIR    # change the output folder
    python3 drawkit/export.py --only slug  # one character only

Per character: one transparent SVG for each expression, plus an expression sheet.
For the whole cast: a line-up of the leads (cast-lineup), a silhouette test
(silhouettes) and one supporting-cast image per episode (episode-<id>-cast).
PNGs are captured with headless Chrome/Chromium; set the CHROME environment
variable if the browser is installed somewhere unusual.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from core import EXPRESSIONS, EXPRESSION_ORDER, INK, character, check, total_height  # noqa: E402
import cast as cast_module  # noqa: E402

CAST = cast_module.CAST
CHANNEL = getattr(cast_module, "CHANNEL", {})
MAIN = [P for P in CAST if not P.get("episode")] or CAST     # leads: not tied to any episode
EPISODES = sorted(set(P["episode"] for P in CAST if P.get("episode")))
FONT = "'Helvetica Neue', Arial, sans-serif"
PAPER, PAPER_LINE = "#efe6d2", "#d8cbb0"


def find_chrome():
    cands = [os.environ.get("CHROME"),
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Chromium.app/Contents/MacOS/Chromium",
             "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    cands += [shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser", "chrome")]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def svg(w, h, inner, bg=None):
    rect = '<rect width="%d" height="%d" fill="%s"/>' % (w, h, bg) if bg else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s%s</svg>'
            % (w, h, w, h, rect, inner))


def text(x, y, s, size, fill=INK, weight=700, anchor="middle", extra=""):
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%d" font-weight="%d" fill="%s" '
            'text-anchor="%s" %s>%s</text>' % (x, y, FONT, size, weight, fill, anchor, extra, s))


def write(path, content):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w") as f:
        f.write(content)
    return path


def to_png(chrome, svg_path, w, h):
    png = svg_path[:-4] + ".png"
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--force-device-scale-factor=1", "--window-size=%d,%d" % (w, h),
           "--screenshot=" + png, "file://" + svg_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    return png


def single(P, expr, D=300):
    w, h = int(D * 2.1), int(D * 3.0)
    return w, h, svg(w, h, character(P, expr, x=w * 0.44, y=h - D * 0.12, D=D))


def sheet(P):
    cols, cw, ch, head_h, D = 4, 330, 440, 120, 132
    rows = (len(EXPRESSION_ORDER) + cols - 1) // cols
    w, h = cols * cw, head_h + rows * ch + 20
    inner = text(40, 62, "CHARACTER FILE · %s" % P["name"].upper(), 34, anchor="start")
    inner += text(40, 96, "Height %.2f D · %d expressions · 3/4 view facing right" % (
        total_height(P), len(EXPRESSION_ORDER)), 19, weight=400, anchor="start")
    for i, key in enumerate(EXPRESSION_ORDER):
        cx, cy = (i % cols) * cw, head_h + (i // cols) * ch
        inner += '<rect x="%d" y="%d" width="%d" height="%d" rx="14" fill="#f8f2e2" stroke="%s" stroke-width="2"/>' % (
            cx + 10, cy + 6, cw - 20, ch - 12, PAPER_LINE)
        inner += character(P, key, x=cx + cw * 0.44, y=cy + ch - 62, D=D)
        inner += text(cx + cw / 2.0, cy + ch - 24, EXPRESSIONS[key]["label"], 21)
    return w, h, svg(w, h, inner, PAPER)


def row_layout(cast, w, top, ground):
    """Share the row evenly. Return D and a list of (P, x, flip): the right half faces the middle."""
    n = len(cast)
    slot = w / float(n)
    tallest = max(total_height(P) for P in cast)
    D = min(235.0, slot * 0.435, (ground - top) / (tallest + 0.35))
    out = []
    for i, P in enumerate(cast):
        x = slot * (i + 0.5)
        out.append((P, x, n > 1 and x > w / 2.0 + 1))
    return D, out


def lineup():
    w, h, ground = 1080, 1350, 1090
    bg = CHANNEL.get("background", "#141a2a")
    accent = CHANNEL.get("accent", "#f6c343")
    inner = ('<defs><radialGradient id="lamp" cx="50%%" cy="34%%" r="62%%">'
             '<stop offset="0" stop-color="%s" stop-opacity="0.50"/>'
             '<stop offset="0.55" stop-color="%s" stop-opacity="0.10"/>'
             '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient></defs>') % (accent, accent, accent)
    inner += '<rect width="%d" height="%d" fill="url(#lamp)"/>' % (w, h)
    inner += '<rect x="0" y="%d" width="%d" height="%d" fill="#000000" opacity="0.28"/>' % (ground - 20, w, h - ground + 20)
    title = CHANNEL.get("name", "THE CAST").upper()
    size = int(min(86, 1500.0 / max(len(title), 1)))
    inner += text(w / 2.0, 150, title, size, fill=accent, weight=900, extra='letter-spacing="2"')
    if CHANNEL.get("tagline"):
        inner += text(w / 2.0, 205, CHANNEL["tagline"], 32, fill=PAPER, weight=400)
    D, places = row_layout(MAIN, w, 260, ground)
    k = min(1.0, 2.6 / len(MAIN))
    for P, x, flip in places:
        inner += character(P, P.get("lineup_expr", "neutral"), x=x, y=ground, D=D, flip=flip, halo=True)
        inner += text(x, ground + 95, P["name"].upper(), int(40 * k), fill=PAPER, weight=900)
        if P.get("role"):
            inner += text(x, ground + 135, P["role"], int(26 * k), fill="#b9c0d0", weight=400)
    return w, h, svg(w, h, inner, bg)


def episode(ep):
    """The supporting cast of one episode, on a paper background."""
    cast = [P for P in CAST if P.get("episode") == ep]
    w, h, ground = 1080, 760, 590
    D, places = row_layout(cast, w, 130, ground)
    inner = text(40, 62, "EPISODE %s · SUPPORTING CAST" % ep, 30, anchor="start")
    for P, x, flip in places:
        inner += character(P, P.get("lineup_expr", "neutral"), x=x, y=ground, D=D, flip=flip)
        inner += text(x, ground + 70, P["name"], 28)
        if P.get("role"):
            inner += text(x, ground + 104, P["role"], 19, weight=400)
    return w, h, svg(w, h, inner, PAPER)


def silhouettes():
    w, h, ground = 1080, 720, 600
    D, places = row_layout(CAST, w, 110, ground)
    inner = text(40, 58, "SILHOUETTE TEST · can you tell who is who from the shape alone?", 26, anchor="start")
    for P, x, flip in places:
        inner += character(P, "neutral", x=x, y=ground, D=D, flip=flip, silhouette=True)
        inner += text(x, ground + 60, P["name"], 24)
    return w, h, svg(w, h, inner, PAPER)


def arg(flag):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else None


def main():
    out = os.path.abspath(arg("--out") or os.path.join(os.path.dirname(HERE), "out"))
    only = arg("--only")
    cast = [P for P in CAST if not only or P.get("slug") == only]
    if not cast:
        sys.exit("No character has the slug '%s'." % only)

    ok = True
    for P in cast:
        for msg in check(P):
            ok = False
            print("WARNING [%s] %s" % (P.get("name", "?"), msg))
    slugs = [P.get("slug") for P in CAST]
    if len(set(slugs)) != len(slugs):
        ok = False
        print("WARNING: two characters share the same slug")
    print("Declaration check: %s" % ("passed" if ok else "warnings, see above"))

    made = []
    for P in cast:
        for key in EXPRESSION_ORDER:
            w, h, s = single(P, key)
            write(os.path.join(out, P["slug"], key + ".svg"), s)
        w, h, s = sheet(P)
        made.append((write(os.path.join(out, "expression-sheet-%s.svg" % P["slug"]), s), w, h))
    if not only:
        for name, fn in (("cast-lineup", lineup), ("silhouettes", silhouettes)):
            w, h, s = fn()
            made.append((write(os.path.join(out, name + ".svg"), s), w, h))
        for ep in EPISODES:
            w, h, s = episode(ep)
            made.append((write(os.path.join(out, "episode-%s-cast.svg" % ep), s), w, h))

    chrome = None if "--no-png" in sys.argv else find_chrome()
    if "--no-png" not in sys.argv and not chrome:
        print("Chrome/Chromium not found: exported SVG only. Set the CHROME variable to capture PNGs.")
    for path, w, h in made:
        print(to_png(chrome, path, w, h) if chrome else path)
    print("Next: open every PNG and inspect it before showing it to the reviewer.")


if __name__ == "__main__":
    main()
