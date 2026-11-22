#!/usr/bin/env node
// Render a stage page to video: node render.mjs <project-dir> [--fps 24] [--workers 2] [--out out/video.mp4] [--stills 1,5.5,30] [--from s --to s]
// The project dir must contain index.html (copy of stage/index.html) exposing window.READY, window.DUR and window.render(t).
// Uses the system Chrome through playwright-core (npm install in this folder once). Frames are JPEG screenshots piped to ffmpeg.
import http from 'http'; import fs from 'fs'; import path from 'path'; import { spawn, execFileSync } from 'child_process';
import { chromium } from 'playwright-core';
const args = process.argv.slice(2), dir = path.resolve(args[0] || '.'), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const FPS = +opt('--fps', 24), WK = +opt('--workers', 2), out = path.resolve(dir, opt('--out', 'out/video.mp4')), stills = opt('--stills', '');
if (!fs.existsSync(path.join(dir, 'index.html'))) { console.error('no index.html in', dir); process.exit(2); }
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
const server = http.createServer((q, r) => { const p = path.join(dir, decodeURIComponent(q.url.split('?')[0])); const f = p.endsWith(path.sep) ? p + 'index.html' : p;
  if (!f.startsWith(dir) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
await new Promise(r => server.listen(0, '127.0.0.1', r)); const url = `http://127.0.0.1:${server.address().port}/index.html`;
const proj = fs.existsSync(path.join(dir, 'project.json')) ? JSON.parse(fs.readFileSync(path.join(dir, 'project.json'), 'utf8')) : {}, [W, H] = proj.size || [1080, 1920];
async function open() { const b = await chromium.launch({ channel: process.env.CHROME_CHANNEL || 'chrome', executablePath: process.env.CHROME_PATH || undefined });
  const pg = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  pg.on('pageerror', e => { console.error('page error:', e.message); process.exit(1); }); pg.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  await pg.goto(url); await pg.waitForFunction('window.READY === true', null, { timeout: 120000 }); return [b, pg]; }
const shot = async (pg, t) => { await pg.evaluate(t => window.render(t), t); return pg.screenshot({ type: 'jpeg', quality: 93 }); };
fs.mkdirSync(path.dirname(out), { recursive: true });
if (stills) { const [b, pg] = await open(); const d = path.join(dir, 'out', 'stills'); fs.mkdirSync(d, { recursive: true });
  for (const t of stills.split(',').map(Number)) { fs.writeFileSync(path.join(d, `t_${t}.jpg`), await shot(pg, t)); console.log(path.join(d, `t_${t}.jpg`)); }
  await b.close(); server.close(); process.exit(0); }
const [b0, p0] = await open(); const DUR = await p0.evaluate('window.DUR'); await b0.close();
const f0 = Math.round(+opt('--from', 0) * FPS), f1 = Math.round(+opt('--to', DUR) * FPS), N = f1 - f0, per = Math.ceil(N / WK), segs = [];
console.log(`${N} frames, ${WK} worker(s)`);
await Promise.all([...Array(WK)].map(async (_, k) => { const a = f0 + k * per, z = Math.min(f1, a + per); if (a >= z) return; const seg = out.replace(/\.mp4$/, `.seg${k}.mp4`); segs[k] = seg;
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  const [b, pg] = await open(); const t0 = Date.now();
  for (let f = a; f < z; f++) { const buf = await shot(pg, f / FPS); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); if ((f - a) % 240 === 0) console.log(`w${k} ${f - a}/${z - a} ${Math.round((Date.now() - t0) / 1000)}s`); }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); }));
const list = out + '.txt'; fs.writeFileSync(list, segs.filter(Boolean).map(s => `file '${s}'`).join('\n'));
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out]); segs.filter(Boolean).forEach(s => fs.unlinkSync(s)); fs.unlinkSync(list);
console.log('done', out); server.close();
