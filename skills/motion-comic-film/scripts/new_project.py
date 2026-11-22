#!/usr/bin/env python3
"""Start a film project: new_project.py <project-dir> ["Film title"]
Copies the stage page and example files. Existing files are kept."""
import pathlib, shutil, sys, json
S = pathlib.Path(__file__).resolve().parent.parent; P = pathlib.Path(sys.argv[1]); title = sys.argv[2] if len(sys.argv) > 2 else 'UNTITLED'
for d in ('img', 'voice', 'sfx', 'out', 'refs'): (P / d).mkdir(parents=True, exist_ok=True)
for src, dst in ((S / 'stage' / 'index.html', P / 'index.html'), (S / 'templates' / 'lines.example.json', P / 'lines.json'), (S / 'templates' / 'shots.example.json', P / 'shots.json'), (S / 'templates' / 'prompts.example.json', P / 'prompts.json')):
    if not dst.exists(): shutil.copy(src, dst); print('created', dst)
if not (P / 'fonts.css').exists(): (P / 'fonts.css').write_text('/* optional: @font-face rules for project.json "font" and "titleFont" */\n')
if not (P / 'project.json').exists():
    (P / 'project.json').write_text(json.dumps({'title': title, 'size': [1080, 1920], 'endCard': ['Your channel', 'A work of fiction.'], 'titleAt': None, 'boil': 0.9}, indent=1, ensure_ascii=False)); print('created', P / 'project.json')
