// Renders index.html frame-by-frame to video (and optional stills).
//   node scripts/render.mjs                    -> out/prismax-iros2026.mp4
//   node scripts/render.mjs --stills 2,6,10    -> out/stills/t-2.00.png ...
//   node scripts/render.mjs --fps 60 --from 10 --to 14 --out out/clip.mp4
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile, mkdir, access } from 'node:fs/promises';
import { extname, join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => {
  if (v.startsWith('--')) a.push([v.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
  return a;
}, []));

const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2', '.wav': 'audio/wav' };
const server = createServer(async (req, res) => {
  try {
    const p = join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    const body = await readFile(p.endsWith('/') ? join(p, 'index.html') : p);
    res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--font-render-hinting=none', '--disable-lcd-text'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(`http://127.0.0.1:${port}/index.html?render`);
await page.evaluate(() => window.__ready);
const DURATION = await page.evaluate(() => window.__DURATION);
const stage = await page.$('#stage');
const shot = (type = 'jpeg') => stage.screenshot(type === 'png' ? { type: 'png' } : { type: 'jpeg', quality: 94 });
const seek = t => page.evaluate(t => window.__seek(t), t);

if (args.stills) {
  await mkdir(join(ROOT, 'out/stills'), { recursive: true });
  for (const t of String(args.stills).split(',').map(Number)) {
    await seek(t);
    const buf = await shot('png');
    const { writeFile } = await import('node:fs/promises');
    await writeFile(join(ROOT, `out/stills/t-${t.toFixed(2)}.png`), buf);
    console.log('still', t);
  }
} else {
  const fps = +(args.fps || 30);
  const from = +(args.from || 0), to = +(args.to || DURATION);
  const out = resolve(ROOT, args.out || 'out/prismax-iros2026.mp4');
  const audio = join(ROOT, 'out/soundtrack.wav');
  const hasAudio = await access(audio).then(() => true, () => false) && !args.mute;
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    ...(hasAudio ? ['-ss', String(from), '-t', String(to - from), '-i', audio] : []),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
    ...(hasAudio ? ['-c:a', 'aac', '-b:a', '256k', '-shortest'] : []),
    '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const total = Math.round((to - from) * fps);
  const t0 = Date.now();
  for (let i = 0; i < total; i++) {
    await seek(from + i / fps);
    const buf = await shot();
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % fps === 0) process.stdout.write(`\rframe ${i}/${total}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log(`\nwrote ${out}`);
}
await browser.close();
server.close();
