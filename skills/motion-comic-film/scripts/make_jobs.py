#!/usr/bin/env python3
"""Turn prompts.json into a batch file for the flow2api skill: make_jobs.py <project> [--only s03,s07] [--variants] [--model M] [--size 1K]
Writes <project>/out/jobs.jsonl (scenes) or out/jobs-variants.jsonl; run it with  flow2api.py batch <file> --parallel 4.
Each job is one paid generation: tell the user the count and get a yes before running the batch."""
import json, pathlib, sys
P = pathlib.Path(sys.argv[1]).resolve(); pr = json.loads((P / 'prompts.json').read_text()); arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
only = set(arg('--only', '').split(',')) - {''}; model = arg('--model', 'gemini-3.1-flash-image'); size = arg('--size', '1K'); aspect = pr.get('aspect', '9:16')
def find(n):
    for e in ('.jpg', '.png', '.webp'):
        if (P / 'img' / (n + e)).exists(): return str(P / 'img' / (n + e))
    sys.exit(f'img/{n} not generated yet')
jobs = []
if '--variants' in sys.argv:
    for v in pr.get('variants', []):
        if only and v['of'] not in only: continue
        jobs.append({'kind': 'image', 'prompt': pr['edit'] + v['change'], 'model': model, 'aspect': aspect, 'size': size, 'ref': [find(v['of'])], 'out': str(P / 'img'), 'name': v.get('name', v['of'] + 'b')})
    out = P / 'out' / 'jobs-variants.jsonl'
else:
    for s in pr['shots']:
        if only and s['name'] not in only: continue
        jobs.append({'kind': 'image', 'prompt': pr['style'] + s['scene'], 'model': model, 'aspect': aspect, 'size': size, 'ref': [str(P / r) for r in s.get('refs', [])], 'out': str(P / 'img'), 'name': s['name']})
    out = P / 'out' / 'jobs.jsonl'
out.parent.mkdir(exist_ok=True); out.write_text('\n'.join(json.dumps(j, ensure_ascii=False) for j in jobs) + '\n'); print(len(jobs), 'paid generations ->', out)
