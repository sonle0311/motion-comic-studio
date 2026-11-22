#!/usr/bin/env python3
"""Build timing, subtitle cues and the voice track from one recording per line.

  timeline.py <project>     reads  <project>/lines.json   [{"id": "001", "text": "...", "gap": 0.4, "mute_from": 2.1}, ...]
                                   <project>/voice/<id>.wav (or .mp3)
                            writes <project>/timing.json  {"dur": s, "lines": {id: {"t": start, "d": duration}}}
                                   <project>/cues.json    [{"t0", "t1", "text"}]
                                   <project>/out/voice.wav (48 kHz mono, every line at its start time)
"gap" is the pause before a line (default 0.4 s; 1.6 s when "brk": 2 marks a new section). "mute_from" silences the
recording from that second: use it when a line ends in an onomatopoeia that a sound effect will play instead.
The first line starts at project.json "start" (default 0.3 s) so the film opens with sound. "tail" seconds follow the last line (default 7).
"""
import json, pathlib, subprocess, sys
P = pathlib.Path(sys.argv[1]); cfg = json.loads((P / 'project.json').read_text()) if (P / 'project.json').exists() else {}
lines = json.loads((P / 'lines.json').read_text()); (P / 'out').mkdir(exist_ok=True)
def src(i):
    for e in ('.wav', '.mp3', '.m4a', '.flac'):
        if (P / 'voice' / (i + e)).exists(): return P / 'voice' / (i + e)
    sys.exit(f'missing voice/{i}.wav')
def dur(f): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)], capture_output=True, text=True).stdout)
t = cfg.get('start', 0.3); timing, cues, ins, flt = {}, [], [], []
for n, l in enumerate(lines):
    f = src(l['id']); d = dur(f)
    t += 0 if n == 0 else l.get('gap', 1.6 if l.get('brk') == 2 else 0.4)
    timing[l['id']] = {'t': round(t, 3), 'd': round(d, 3)}; cues.append({'t0': round(t - .05, 3), 't1': round(t + d + .3, 3), 'text': l['text']})
    ins += ['-i', str(f)]; m = f",volume=enable='gte(t,{l['mute_from']})':volume=0" if 'mute_from' in l else ''
    flt.append(f"[{n}]aresample=48000,aformat=channel_layouts=mono{m},adelay={int(t * 1000)}[a{n}]"); t += d
total = round(t + cfg.get('tail', 7.0), 3)
# mix in groups of 30 inputs to stay under ffmpeg's practical limits
parts = []
for g in range(0, len(lines), 30):
    idx = list(range(g, min(g + 30, len(lines)))); out = P / 'out' / f'.voice{g}.wav'; parts.append(out)
    fc = ';'.join(flt[i].replace(f'[{i}]', f'[{i - g}]', 1) for i in idx) + ';' + ''.join(f'[a{i}]' for i in idx) + f'amix=inputs={len(idx)}:normalize=0,apad=whole_dur={total}[o]'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + sum((ins[2 * i:2 * i + 2] for i in idx), []) + ['-filter_complex', fc, '-map', '[o]', '-t', str(total), '-ar', '48000', str(out)], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + sum((['-i', str(p)] for p in parts), []) + ['-filter_complex', f'amix=inputs={len(parts)}:normalize=0', '-t', str(total), str(P / 'out' / 'voice.wav')], check=True)
for p in parts: p.unlink()
(P / 'timing.json').write_text(json.dumps({'dur': total, 'lines': timing}, indent=1)); (P / 'cues.json').write_text(json.dumps(cues, ensure_ascii=False, indent=1))
print(f'{len(lines)} lines, {total:.1f} s, voice {sum(v["d"] for v in timing.values()):.1f} s')
