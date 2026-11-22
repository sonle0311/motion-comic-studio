#!/usr/bin/env python3
"""Mix voice with optional ambience, music and timed sound effects, then mux onto the picture.

  mix.py <project> [--amb rain.wav] [--music bed.mp3] [--amb-db -26] [--music-db -24] [--video out/video.mp4] [--final film.mp4]
Sound effects: <project>/sfx.json  [{"file": "sfx/knock.wav", "at": "015", "dt": 2.3, "db": -6}]  ("at" is a line id or a number of seconds).
Ambience and music loop for the whole film and fade in/out. The voice gets a gentle high-pass and a small cut at 220 Hz so it is not boomy.
Master: -14 LUFS, true peak -1.5 dBFS. Check the result with: ffmpeg -i film.mp4 -af ebur128=peak=true -f null -
"""
import argparse, json, pathlib, subprocess
ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--amb'); ap.add_argument('--music'); ap.add_argument('--amb-db', type=float, default=-26); ap.add_argument('--music-db', type=float, default=-24)
ap.add_argument('--video', default='out/video.mp4'); ap.add_argument('--final', default='film.mp4'); a = ap.parse_args()
P = pathlib.Path(a.project); tm = json.loads((P / 'timing.json').read_text()); D = tm['dur']
ins = ['-i', str(P / 'out' / 'voice.wav')]; flt = ['[0]highpass=f=85,equalizer=f=220:t=q:w=1.0:g=-2.5[v]']; mixin = ['[v]']; n = 1
for f, db, tag in ((a.amb, a.amb_db, 'amb'), (a.music, a.music_db, 'mus')):
    if f:
        ins += ['-stream_loop', '-1', '-i', f]; flt.append(f'[{n}]atrim=0:{D},volume={db}dB,afade=t=in:d=1.5,afade=t=out:st={D - 3}:d=3[{tag}]'); mixin.append(f'[{tag}]'); n += 1
sfx = json.loads((P / 'sfx.json').read_text()) if (P / 'sfx.json').exists() else []
for k, e in enumerate(sfx):
    at = (tm['lines'][e['at']]['t'] if isinstance(e['at'], str) else e['at']) + e.get('dt', 0)
    ins += ['-i', str(P / e['file'])]; flt.append(f"[{n}]volume={e.get('db', -6)}dB,adelay={int(at * 1000)}:all=1[s{k}]"); mixin.append(f'[s{k}]'); n += 1
flt.append(''.join(mixin) + f'amix=inputs={len(mixin)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,aformat=sample_rates=48000:channel_layouts=stereo[o]')
mixf = P / 'out' / 'mix.wav'
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + ins + ['-filter_complex', ';'.join(flt), '-map', '[o]', '-t', str(D), str(mixf)], check=True)
v = P / a.video
if v.exists():
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(v), '-i', str(mixf), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', str(P / a.final)], check=True)
    print('wrote', P / a.final)
else: print('wrote', mixf, '(no picture yet)')
