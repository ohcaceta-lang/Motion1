/* Shared motion helpers for all videos (deterministic: everything is a function of t). */
const NM = 'node_modules/@fontsource/';
(function fonts() {
  const css = [
    ['Play', 900, 'italic', 'playfair-display/files/playfair-display-latin-900-italic.woff2'],
    ['Play', 900, 'normal', 'playfair-display/files/playfair-display-latin-900-normal.woff2'],
    ['Anton', 400, 'normal', 'anton/files/anton-latin-400-normal.woff2'],
    ['Type', 400, 'normal', 'special-elite/files/special-elite-latin-400-normal.woff2'],
    ['Hand', 700, 'normal', 'caveat/files/caveat-latin-700-normal.woff2'],
    ['DMS', 400, 'normal', 'dm-serif-display/files/dm-serif-display-latin-400-normal.woff2'],
    ['DMS', 400, 'italic', 'dm-serif-display/files/dm-serif-display-latin-400-italic.woff2'],
  ].map(([f, w, s, u]) => `@font-face{font-family:'${f}';font-weight:${w};font-style:${s};src:url('${NM}${u}') format('woff2')}`).join('');
  const st = document.createElement('style'); st.textContent = css + `
    *{box-sizing:border-box;margin:0;padding:0}
    html,body{width:720px;height:1280px;overflow:hidden;background:#000}
    #stage{position:relative;width:720px;height:1280px;overflow:hidden;font-family:Inter,sans-serif}
    .scene{position:absolute;inset:0;overflow:hidden;display:none;transform-origin:50% 50%}
    .abs{position:absolute}
    .line{position:absolute;display:flex;align-items:baseline;white-space:nowrap}
    .w{display:inline-block;white-space:nowrap}
    .ht{position:absolute;inset:0;background-image:radial-gradient(circle,rgba(0,0,0,.55) 1.3px,transparent 1.7px);background-size:5px 5px;mix-blend-mode:multiply;pointer-events:none}
    #flash,#vignette,#grain{position:absolute;inset:0;pointer-events:none}
    #grain{inset:-60px;opacity:.08;mix-blend-mode:overlay}`;
  document.head.appendChild(st);
  document.body.insertAdjacentHTML('afterbegin', `<div id="stage"></div><svg width="0" height="0" style="position:absolute"><defs>
    <filter id="grainF"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/><feColorMatrix type="saturate" values="0"/></filter>
    <filter id="rough"><feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="3" seed="2"/><feDisplacementMap in="SourceGraphic" scale="8"/></filter>
    <filter id="paperF"><feTurbulence type="fractalNoise" baseFrequency=".6" numOctaves="3" seed="4"/><feColorMatrix type="matrix" values="0 0 0 0 .45  0 0 0 0 .38  0 0 0 0 .28  0 0 0 .35 0"/></filter>
  </defs></svg>`);
})();

const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const easeOut = p => 1 - Math.pow(1 - p, 3);
const easeIn = p => p * p * p;
const easeInOut = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
const easeOutExpo = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);
const backOut = p => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
const prog = (t, a, b) => clamp((t - a) / (b - a));
const hex = h => { if (h.length === 4) h = '#' + h[1] + h[1] + h[2] + h[2] + h[3] + h[3]; return [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)); };
const mix = (c1, c2, p) => { const a = hex(c1), b = hex(c2); return `rgb(${a.map((v, i) => Math.round(lerp(v, b[i], p))).join(',')})`; };
const stage = document.getElementById('stage');
const el = (tag, cls, parent, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; (parent || stage).appendChild(e); return e; };
const tw = c => `node_modules/@twemoji/svg/${c}.svg`;
const pop = (t, t0, d = 0.35) => t < t0 ? 0 : backOut(prog(t, t0, t0 + d));

const scenes = [];
function scene(start, end, bg, zoom = 0.02) {
  const d = el('div', 'scene'); d.style.background = bg;
  const s = { start, end, el: d, words: [], updates: [], zoom }; scenes.push(s); return s;
}
const FONTS = {
  sans: (sz, wt = 600) => ({ ff: 'Inter', fw: wt, fs: 'normal', sz, ls: '-0.03em' }),
  serif: sz => ({ ff: 'Play', fw: 900, fs: 'italic', sz, ls: '-0.01em' }),
  caps: sz => ({ ff: 'Anton', fw: 400, fs: 'normal', sz, ls: '0.01em' }),
  type: sz => ({ ff: 'Type', fw: 400, fs: 'normal', sz, ls: '0' }),
  hand: sz => ({ ff: 'Hand', fw: 700, fs: 'normal', sz, ls: '0' }),
  dms: (sz, it) => ({ ff: 'DMS', fw: 400, fs: it ? 'italic' : 'normal', sz, ls: '-0.01em' }),
};
/* Kinetic line: words reveal blur->sharp, scale 1.2->1, color dim->final; line re-centers as words grow in. */
function line(s, x, y, words, o = {}) {
  const L = el('div', 'line', s.el); L.style.left = x + 'px'; L.style.top = y + 'px';
  const items = words.map(([text, t0, w = {}]) => {
    const f = w.font || o.font || FONTS.sans(40);
    const sp = el('span', 'w', L, text.replace(/ /g, '&nbsp;'));
    Object.assign(sp.style, { fontFamily: f.ff, fontWeight: f.fw, fontStyle: f.fs, fontSize: f.sz + 'px', letterSpacing: f.ls });
    return { sp, t0, size: f.sz, color: w.color || o.color || '#ffffff', glow: w.glow ?? o.glow, gap: w.gap ?? f.sz * 0.26,
      from: w.from || o.from || '#3a3433', dur: w.dur || o.dur || 0.28, out: w.out ?? o.out };
  });
  const rec = { L, items, align: o.align || 'center', natural: null, extra: null, outAt: o.outAt };
  s.words.push(rec); return rec;
}
function updateLine(rec, t) {
  if (!rec.natural) rec.natural = rec.items.map(it => { it.sp.style.width = 'auto'; return it.sp.offsetWidth; });
  let vis = false;
  rec.items.forEach((it, i) => {
    const p = prog(t, it.t0, it.t0 + it.dur), e = easeOutExpo(p);
    const pw = easeOutExpo(prog(t, it.t0, it.t0 + it.dur * 0.7));
    it.sp.style.width = rec.natural[i] * pw + 'px';
    it.sp.style.marginRight = (i < rec.items.length - 1 ? pw * it.gap : 0) + 'px';
    it.sp.style.opacity = clamp(p * 3);
    it.sp.style.filter = `blur(${(1 - e) * 10}px)`;
    it.sp.style.transform = `translateY(${(1 - e) * it.size * 0.25}px) scale(${1 + (1 - e) * 0.2})`;
    it.sp.style.color = mix(it.from, it.color, e);
    if (it.glow) it.sp.style.textShadow = `0 0 ${16 * e}px ${it.glow}, 0 0 ${40 * e}px ${it.glow}`;
    if (p > 0) vis = true;
  });
  let o = 1, b = 0;
  if (rec.outAt != null) { const q = prog(t, rec.outAt, rec.outAt + 0.18); o = 1 - q; b = q * 12; }
  const tx = rec.align === 'center' ? '-50%' : rec.align === 'right' ? '-100%' : '0';
  rec.L.style.transform = `translate(${tx}, -50%) ${rec.extra ? rec.extra(t) : ''}`;
  rec.L.style.opacity = o; if (b) rec.L.style.filter = `blur(${b}px)`; else rec.L.style.filter = '';
  rec.L.style.visibility = vis && o > 0.01 ? 'visible' : 'hidden';
}
/* typewriter text: returns element; call typeAt(t) */
function typer(parent, css, text, t0, cps = 22) {
  const d = el('div', 'abs', parent); d.style.cssText = css;
  return { d, at: t => { const n = Math.floor(clamp((t - t0) * cps, 0, text.length)); d.textContent = text.slice(0, n); return n; } };
}

let globalUpdate = null;
function finalize({ fps = 30, duration, flashes = [], grain = 0.08, vignette = 0.4, preload = [] }) {
  const flash = el('div', '', stage); flash.id = 'flash';
  const vg = el('div', '', stage); vg.id = 'vignette'; vg.style.background = `radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 52%, rgba(0,0,0,${vignette}) 100%)`;
  const gr = el('div', '', stage, `<svg width="840" height="1400"><rect width="100%" height="100%" filter="url(#grainF)"/></svg>`); gr.id = 'grain'; gr.style.opacity = grain;
  window.renderAt = t => {
    scenes.forEach(s => {
      const on = t >= s.start && t < s.end; s.el.style.display = on ? 'block' : 'none'; if (!on) return;
      s.el.style.transform = `scale(${1 + (t - s.start) * s.zoom})`; s.el.style.filter = ''; s.el.style.opacity = 1;
      s.updates.forEach(u => u(t)); s.words.forEach(w => updateLine(w, t));
    });
    let f = 0, col = '255,255,255';
    flashes.forEach(([at, dur, c]) => { if (t >= at - 0.06 && t < at + dur) { f = Math.max(f, t < at ? prog(t, at - 0.06, at) : 1 - prog(t, at, at + dur)); if (c) col = c; } });
    flash.style.background = `rgba(${col},${f * 0.85})`;
    gr.style.transform = `translate(${(Math.sin(t * 97) * 30) | 0}px, ${(Math.cos(t * 71) * 30) | 0}px)`;
    if (globalUpdate) globalUpdate(t);
  };
  window.FPS = fps; window.DURATION = duration;
  window.ready = Promise.all([document.fonts.ready, ...['900 italic 40px Play', '40px Anton', '40px Type', '700 40px Hand', '40px DMS', 'italic 40px DMS'].map(f => document.fonts.load(f)),
    ...[...document.images, ...preload.map(src => { const i = new Image(); i.src = src; return i; })].map(i => i.complete ? 1 : new Promise(r => { i.onload = i.onerror = r; }))])
    .then(() => { window.renderAt(0); return true; });
}

/* ---------- narration-driven helpers (need window.WORDS) ---------- */
const ws = i => window.WORDS[i].s;
const we = i => window.WORDS[i].e;
const clean = w => w.replace(/^["“]/, '').replace(/["”]$/, '').replace(/[.,:]+$/, '').replace(/\.\.\.$/, '…');
/* line built from narration words i0..i1 (inclusive); per[i] = per-word overrides; o.text[i] = replacement text */
function seq(s, x, y, i0, i1, o = {}, per = {}) {
  const list = [];
  for (let i = i0; i <= i1; i++) list.push([(o.text && o.text[i]) || (o.raw ? window.WORDS[i].w : clean(window.WORDS[i].w)), ws(i) - (o.lead ?? 0.04), per[i] || {}]);
  return line(s, x, y, list, o);
}
/* full-bleed photo with Ken Burns move */
function bg(s, src, o = {}) {
  const im = el('img', 'abs', s.el); im.src = src;
  im.style.cssText = `left:-40px;top:-70px;width:800px;height:1420px;object-fit:cover;transform-origin:${o.origin || '50% 50%'};filter:${o.filter || 'none'}`;
  const z0 = o.z0 ?? 1.12, z1 = o.z1 ?? 1.0, px = o.px ?? 0, py = o.py ?? 0;
  s.updates.push(t => { const p = easeInOut(prog(t, s.start, s.end)); im.style.transform = `translate(${px * p}px, ${py * p}px) scale(${lerp(z0, z1, p)})`; });
  return im;
}
function shade(s, css) { const d = el('div', 'abs', s.el); d.style.cssText = 'inset:0;' + css; return d; }

/* ---------- verificação automática de layout (quebra de texto e espaçamento) ----------
   window.layoutCheck({margem=40, folga=0.22}) percorre cada linha de texto no instante em que ela termina de
   aparecer (e no fim da cena) e acusa:
   - CORTE:      linha passa da margem segura lateral (40 px de cada lado no canvas de 720) ou sai da tela em cima/embaixo;
   - SOBREPOSIÇÃO: duas linhas visíveis ao mesmo tempo se cruzam;
   - APERTADO:   distância vertical entre linhas vizinhas menor que 22% da altura da linha menor;
   - ELEMENTO:   texto cruzando um elemento marcado com data-evitar (fotos, cartões, carimbos que não devem cobrir texto).
   Retorna uma lista de problemas [{t, tipo, texto, detalhe}]. */
window.layoutCheck = function (o = {}) {
  const M = o.margem ?? 40, F = o.folga ?? 0.22, out = [];
  const visRect = el => { const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity < 0.5) return null;
    let p = el; while (p && p !== stage) { const c = getComputedStyle(p); if (c.display === 'none' || +c.opacity < 0.3) return null; p = p.parentElement; }
    const r = el.getBoundingClientRect(); return r.width > 2 && r.height > 2 ? r : null; };
  const txt = rec => rec.items.map(i => i.sp.textContent.replace(/ /g, ' ')).join(' ');
  const tight = r => { // caixa da linha sem o "ar" da fonte: ~72% da altura, centrada
    const h = r.height * 0.72; return { left: r.left, right: r.right, top: r.top + (r.height - h) / 2, bottom: r.bottom - (r.height - h) / 2, height: h }; };
  scenes.forEach(s => {
    const instantes = new Set();
    s.words.forEach(rec => { const t = Math.max(...rec.items.map(i => i.t0 + i.dur)) + 0.06; if (t > s.start && t < s.end) instantes.add(+t.toFixed(2)); });
    instantes.add(+(s.end - 0.05).toFixed(2));
    [...instantes].sort((a, b) => a - b).forEach(t => {
      window.renderAt(t);
      const linhas = s.words.map(rec => ({ rec, r: visRect(rec.L) })).filter(x => x.r && x.rec.items.every(i => t >= i.t0 + i.dur));
      linhas.forEach(({ rec, r }) => {
        if (r.left < M || r.right > 720 - M) out.push({ t, tipo: 'CORTE', texto: txt(rec), detalhe: `x ${Math.round(r.left)}–${Math.round(r.right)} (limite ${M}–${720 - M}); largura ${Math.round(r.width)} px` });
        if (r.top < 20 || r.bottom > 1260) out.push({ t, tipo: 'CORTE', texto: txt(rec), detalhe: `y ${Math.round(r.top)}–${Math.round(r.bottom)}` });
      });
      for (let i = 0; i < linhas.length; i++) for (let j = i + 1; j < linhas.length; j++) {
        const a = tight(linhas[i].r), b = tight(linhas[j].r);
        if (a.right <= b.left || b.right <= a.left) continue;              // não dividem coluna
        const gap = a.top < b.top ? b.top - a.bottom : a.top - b.bottom;
        const min = F * Math.min(a.height, b.height);
        if (gap < 0) out.push({ t, tipo: 'SOBREPOSIÇÃO', texto: `"${txt(linhas[i].rec)}" × "${txt(linhas[j].rec)}"`, detalhe: `cruzam ${Math.round(-gap)} px` });
        else if (gap < min) out.push({ t, tipo: 'APERTADO', texto: `"${txt(linhas[i].rec)}" × "${txt(linhas[j].rec)}"`, detalhe: `espaço ${Math.round(gap)} px (mínimo ${Math.round(min)} px)` });
      }
      [...s.el.querySelectorAll('[data-evitar]')].forEach(e => { const er = visRect(e); if (!er) return;
        linhas.forEach(({ rec, r }) => { const a = tight(r);
          if (a.left < er.right && a.right > er.left && a.top < er.bottom && a.bottom > er.top)
            out.push({ t, tipo: 'ELEMENTO', texto: txt(rec), detalhe: `cruza ${e.dataset.evitar || 'elemento'}` }); }); });
    });
  });
  const seen = new Set(); return out.filter(p => { const k = p.tipo + p.texto; if (seen.has(k)) return false; seen.add(k); return true; });
};
