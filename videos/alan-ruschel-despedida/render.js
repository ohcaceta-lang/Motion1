// node render.js page.html out.mp4  |  node render.js page.html prefixo --preview 1,2,3  |  node render.js page.html --check
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const out = process.argv[3];
  const prevIdx = process.argv.indexOf('--preview');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await page.goto('file://' + path.resolve(process.argv[2]));
  await page.evaluate(() => window.ready);
  const draw = t => page.evaluate(async t => {
    renderAt(t);
    await Promise.all([...document.images].filter(i => i.src).map(i => i.decode().catch(() => {})));
  }, t);
  if (process.argv.includes('--check')) {               // verificação automática de quebra de texto e espaçamento
    const probs = await page.evaluate(() => window.layoutCheck());
    if (!probs.length) console.log('LAYOUT OK: nenhum corte, sobreposição, espaçamento apertado ou espaçamento exagerado.');
    else { console.log(`LAYOUT: ${probs.length} problema(s)`); probs.forEach(p => console.log(`  [${p.tipo}] t=${p.t}s  ${p.texto}  →  ${p.detalhe}`)); }
    await browser.close(); process.exit(probs.length ? 2 : 0);
  }
  if (prevIdx > 0) {
    for (const t of process.argv[prevIdx + 1].split(',').map(Number)) {
      await draw(t);
      await page.screenshot({ path: `${out}_${t.toFixed(2).padStart(5, '0')}.png` });
    }
    return browser.close();
  }
  const { FPS, DURATION } = await page.evaluate(() => ({ FPS, DURATION }));
  const n = Math.round(FPS * DURATION);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) {
    await draw(i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 100 === 0) process.stderr.write(`frame ${i}/${n}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
