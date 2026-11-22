#!/usr/bin/env python3
"""Prepare generated stills for the stage: prep_images.py <project> [--no-patch] [--sheet]
  img/<name>.(jpg|png)  ->  img/hi/<name>.jpg   upscaled 2x with lanczos and lightly sharpened (keeps ink lines crisp at 1080x1920)
Before upscaling, the bottom-right corner is patched with a mirrored copy of the area to its left, to hide the small watermark some
image services stamp there (needs Pillow; skipped without it or with --no-patch). --sheet also writes out/sheet-NN.jpg contact sheets
of ten images each for review. Look at the result at full size too: a contact sheet hides blur.
"""
import pathlib, subprocess, sys
P = pathlib.Path(sys.argv[1]); img = P / 'img'; hi = img / 'hi'; hi.mkdir(parents=True, exist_ok=True); (P / 'out').mkdir(exist_ok=True)
files = sorted(p for p in img.iterdir() if p.is_file() and not p.name.startswith('.') and p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'))
try:
    from PIL import Image, ImageFilter, ImageDraw
except ImportError: Image = None
for p in files:
    dst = hi / (p.stem + '.jpg')
    if dst.exists() and dst.stat().st_mtime >= p.stat().st_mtime: continue
    src = p
    if Image and '--no-patch' not in sys.argv:
        im = Image.open(p).convert('RGB'); w, h = im.size; bw, bh = int(w * .16), int(h * .085); x0, y0 = w - bw, h - bh
        patch = im.crop((x0 - bw, y0, x0, h)).transpose(Image.FLIP_LEFT_RIGHT); mask = Image.new('L', (bw, bh), 0); mask.paste(255, (int(bw * .18), int(bh * .18), bw, bh))
        im.paste(patch, (x0, y0), mask.filter(ImageFilter.GaussianBlur(bw * .08))); src = P / 'out' / ('.patched-' + p.stem + '.png'); im.save(src)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(src), '-vf', 'scale=iw*2:ih*2:flags=lanczos,unsharp=5:5:0.9:5:5:0.0', '-q:v', '2', str(dst)], check=True)
    if src != p: src.unlink()
    print(dst)
if '--sheet' in sys.argv and Image:
    for k in range(0, len(files), 10):
        sh = Image.new('RGB', (5 * 300, 2 * 540))
        for i, p in enumerate(files[k:k + 10]):
            im = Image.open(p).convert('RGB'); im.thumbnail((300, 540)); ImageDraw.Draw(im).text((6, 4), p.stem, fill=(255, 255, 0)); sh.paste(im, ((i % 5) * 300, (i // 5) * 540))
        sh.save(P / 'out' / f'sheet-{k // 10:02d}.jpg', quality=85); print(P / 'out' / f'sheet-{k // 10:02d}.jpg')
