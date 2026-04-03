// @ts-check

/** @param {string} hex @returns {[number,number,number]} */
const hexToRgb = hex => {
  const n = parseInt(hex.replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};

/** Linear interpolate between two hex colors. t ∈ [0,1] */
function lerpColor(a, b, t) {
  const [ar, ag, ab] = hexToRgb(a);
  const [br, bg, bb] = hexToRgb(b);
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return `rgb(${r},${g},${bl})`;
}

/** Format number with optional decimal places */
function fmt(n, decimals = 0) {
  if (n == null || isNaN(n)) return '—';
  return Number(n).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

// === TOOLTIP SYSTEM ===

let _tooltipEl = null;

function _getTooltip() {
  if (!_tooltipEl) {
    _tooltipEl = document.createElement('div');
    _tooltipEl.className = 'tooltip';
    _tooltipEl.style.display = 'none';
    document.body.appendChild(_tooltipEl);
  }
  return _tooltipEl;
}

/** Scan [data-tooltip] elements and attach floating tooltip on hover */
function initTooltips() {
  document.querySelectorAll('[data-tooltip]').forEach(el => {
    el.classList.add('tooltip-trigger');
    el.addEventListener('mouseenter', e => {
      const tip = _getTooltip();
      tip.textContent = /** @type {HTMLElement} */ (el).dataset.tooltip ?? '';
      tip.style.display = 'block';
    });
    el.addEventListener('mousemove', e => {
      const tip = _getTooltip();
      const mx = /** @type {MouseEvent} */ (e).clientX;
      const my = /** @type {MouseEvent} */ (e).clientY;
      const rect = tip.getBoundingClientRect();
      const tw = rect.width;
      const th = rect.height;
      const arrowH = 7; // px — matches CSS border-width in ::after
      const pad = 8;
      const vw = window.innerWidth;
      const vh = window.innerHeight;

      // Horizontal: center the tooltip on the cursor, clamped to viewport
      let left = mx - tw / 2;
      left = Math.max(pad, Math.min(left, vw - tw - pad));

      // Vertical: bottom tip (arrow) at cursor — tooltip appears above
      let top = my - th - arrowH - 2;
      if (top < pad) {
        // Not enough space above — flip below cursor
        top = my + arrowH + 6;
        tip.classList.add('tooltip-below');
      } else {
        tip.classList.remove('tooltip-below');
      }
      // Clamp so tooltip never goes below viewport
      top = Math.min(top, vh - th - pad);

      tip.style.left = `${left}px`;
      tip.style.top = `${top}px`;
    });
    el.addEventListener('mouseleave', () => {
      _getTooltip().style.display = 'none';
    });
  });
}

// === POPUP / DIALOG SYSTEM ===

/** @param {string} id */
function openPopup(id) {
  const el = /** @type {HTMLDialogElement|null} */ (document.getElementById(id));
  el?.showModal();
}

/** @param {string} id */
function closePopup(id) {
  const el = /** @type {HTMLDialogElement|null} */ (document.getElementById(id));
  el?.close();
}

/** Close dialog when clicking the backdrop (the dialog element itself outside content) */
function initPopups() {
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.addEventListener('click', e => {
      if (e.target === dialog) dialog.close();
    });
    dialog.querySelectorAll('.dialog-close').forEach(btn => {
      btn.addEventListener('click', () => dialog.close());
    });
  });
}

// === SVG CHART UTILITIES ===

const DEFAULTS = {
  width: 600,
  height: 320,
  marginTop: 20,
  marginRight: 20,
  marginBottom: 40,
  marginLeft: 50,
  colors: ['#2d3a8c', '#d64045', '#2a9d5c', '#f5c842', '#e76f51', '#457b9d'],
};

/** @param {number} min @param {number} max @param {number} ticks */
function _niceTicks(min, max, ticks = 5) {
  if (min === max) { min -= 1; max += 1; }
  const range = max - min;
  const step = Math.pow(10, Math.floor(Math.log10(range / ticks)));
  const nice = [1, 2, 2.5, 5, 10].find(f => range / (step * f) <= ticks) ?? 10;
  const interval = step * nice;
  const lo = Math.floor(min / interval) * interval;
  const hi = Math.ceil(max / interval) * interval;
  const result = [];
  for (let v = lo; v <= hi + 1e-9; v += interval) result.push(+v.toPrecision(10));
  return result;
}

/** Escape text for SVG */
const _esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/**
 * Bar chart (vertical or horizontal).
 * @param {HTMLElement} container
 * @param {{label:string, value:number, color?:string}[]} data
 * @param {{width?:number,height?:number,horizontal?:boolean,title?:string,unit?:string,maxValue?:number,colors?:string[]}} [options]
 */
function createBarChart(container, data, options = {}) {
  if (!data?.length) { container.innerHTML = '<p class="chart-caption">No data</p>'; return; }

  const W = options.width ?? DEFAULTS.width;
  const H = options.height ?? DEFAULTS.height;
  const ml = options.horizontal ? 120 : DEFAULTS.marginLeft;
  const mr = DEFAULTS.marginRight;
  const mt = options.title ? 36 : DEFAULTS.marginTop;
  const mb = options.horizontal ? 36 : DEFAULTS.marginBottom;
  const innerW = W - ml - mr;
  const innerH = H - mt - mb;
  const colors = options.colors ?? DEFAULTS.colors;
  const maxVal = options.maxValue ?? Math.max(...data.map(d => d.value));
  const ticks = _niceTicks(0, maxVal);
  const domainMax = ticks.at(-1) ?? maxVal;
  const unit = options.unit ?? '';

  let body = '';

  if (!options.horizontal) {
    const bw = innerW / data.length;
    const gap = Math.max(2, bw * 0.15);
    const barW = bw - gap * 2;

    // Grid lines & y-axis ticks
    ticks.forEach(t => {
      const y = mt + innerH - (t / domainMax) * innerH;
      body += `<line x1="${ml}" y1="${y}" x2="${ml + innerW}" y2="${y}" stroke="#e8e4dd" stroke-width="1"/>`;
      body += `<text x="${ml - 6}" y="${y}" text-anchor="end" dominant-baseline="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${fmt(t)}${unit}</text>`;
    });

    // Bars
    data.forEach((d, i) => {
      const bh = (d.value / domainMax) * innerH;
      const x = ml + i * bw + gap;
      const y = mt + innerH - bh;
      const color = d.color ?? colors[i % colors.length];
      body += `<rect x="${x}" y="${y}" width="${barW}" height="${bh}" fill="${color}" rx="1"${d.tooltip ? ` data-tooltip="${_esc(d.tooltip)}"` : ''}/>`;
      // Value label on bar
      body += `<text x="${x + barW / 2}" y="${y - 4}" text-anchor="middle" font-family="system-ui" font-size="11" fill="#1a1a1a">${fmt(d.value)}${unit}</text>`;
      // X label
      const label = _esc(d.label);
      body += `<text x="${x + barW / 2}" y="${mt + innerH + 14}" text-anchor="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${label.length > 12 ? label.slice(0, 11) + '…' : label}</text>`;
    });
  } else {
    // Horizontal bars
    const bh = innerH / data.length;
    const gap = Math.max(2, bh * 0.2);
    const barH = bh - gap * 2;

    ticks.forEach(t => {
      const x = ml + (t / domainMax) * innerW;
      body += `<line x1="${x}" y1="${mt}" x2="${x}" y2="${mt + innerH}" stroke="#e8e4dd" stroke-width="1"/>`;
      body += `<text x="${x}" y="${mt + innerH + 14}" text-anchor="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${fmt(t)}${unit}</text>`;
    });

    data.forEach((d, i) => {
      const bw = (d.value / domainMax) * innerW;
      const y = mt + i * bh + gap;
      const color = d.color ?? colors[i % colors.length];
      body += `<rect x="${ml}" y="${y}" width="${bw}" height="${barH}" fill="${color}" rx="1"${d.tooltip ? ` data-tooltip="${_esc(d.tooltip)}"` : ''}/>`;
      body += `<text x="${ml - 6}" y="${y + barH / 2}" text-anchor="end" dominant-baseline="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${_esc(d.label)}</text>`;
      body += `<text x="${ml + bw + 4}" y="${y + barH / 2}" dominant-baseline="middle" font-family="system-ui" font-size="11" fill="#1a1a1a">${fmt(d.value)}${unit}</text>`;
    });
  }

  // Axes
  body += `<line x1="${ml}" y1="${mt}" x2="${ml}" y2="${mt + innerH}" stroke="#1a1a1a" stroke-width="1.5"/>`;
  body += `<line x1="${ml}" y1="${mt + innerH}" x2="${ml + innerW}" y2="${mt + innerH}" stroke="#1a1a1a" stroke-width="1.5"/>`;

  const title = options.title
    ? `<text x="${W / 2}" y="16" text-anchor="middle" font-family="system-ui" font-size="13" font-weight="700" fill="#1a1a1a">${_esc(options.title)}</text>`
    : '';

  container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;" role="img">${title}${body}</svg>`;
}

/**
 * Line chart supporting single or multi-series.
 * @param {HTMLElement} container
 * @param {{x:number,y:number,label?:string}[]|{series:{name:string,points:{x:number,y:number}[],color?:string}[]}} data
 * @param {{width?:number,height?:number,title?:string,xLabel?:string,yLabel?:string,xFormat?:(v:number)=>string,yFormat?:(v:number)=>string}} [options]
 */
function createLineChart(container, data, options = {}) {
  if (!data) { container.innerHTML = '<p class="chart-caption">No data</p>'; return; }

  const W = options.width ?? DEFAULTS.width;
  const H = options.height ?? DEFAULTS.height;
  const ml = DEFAULTS.marginLeft + (options.yLabel ? 10 : 0);
  const mr = DEFAULTS.marginRight + 10;
  const mt = options.title ? 36 : DEFAULTS.marginTop;
  const mb = DEFAULTS.marginBottom + (options.xLabel ? 16 : 0);
  const innerW = W - ml - mr;
  const innerH = H - mt - mb;

  // Normalise to multi-series
  /** @type {{name:string,points:{x:number,y:number}[],color?:string}[]} */
  const series = 'series' in data
    ? data.series
    : [{ name: '', points: /** @type {any[]} */ (data), color: DEFAULTS.colors[0] }];

  if (!series.length || !series[0].points?.length) {
    container.innerHTML = '<p class="chart-caption">No data</p>'; return;
  }

  const allX = series.flatMap(s => s.points.map(p => p.x));
  const allY = series.flatMap(s => s.points.map(p => p.y));
  const xTicks = _niceTicks(Math.min(...allX), Math.max(...allX));
  const yTicks = _niceTicks(Math.min(...allY), Math.max(...allY));
  const xMin = xTicks[0], xMax = xTicks.at(-1);
  const yMin = yTicks[0], yMax = yTicks.at(-1);

  const scaleX = v => ml + ((v - xMin) / (xMax - xMin)) * innerW;
  const scaleY = v => mt + innerH - ((v - yMin) / (yMax - yMin)) * innerH;

  const xFmt = options.xFormat ?? (v => fmt(v));
  const yFmt = options.yFormat ?? (v => fmt(v));

  let body = '';

  // Grid
  yTicks.forEach(t => {
    const y = scaleY(t);
    body += `<line x1="${ml}" y1="${y}" x2="${ml + innerW}" y2="${y}" stroke="#e8e4dd" stroke-width="1"/>`;
    body += `<text x="${ml - 6}" y="${y}" text-anchor="end" dominant-baseline="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${_esc(yFmt(t))}</text>`;
  });
  xTicks.forEach(t => {
    const x = scaleX(t);
    body += `<line x1="${x}" y1="${mt}" x2="${x}" y2="${mt + innerH}" stroke="#e8e4dd" stroke-width="1"/>`;
    body += `<text x="${x}" y="${mt + innerH + 14}" text-anchor="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${_esc(xFmt(t))}</text>`;
  });

  // Series
  series.forEach((s, si) => {
    const color = s.color ?? DEFAULTS.colors[si % DEFAULTS.colors.length];
    const pts = s.points.filter(p => p.x != null && p.y != null);
    if (!pts.length) return;
    const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${scaleX(p.x)},${scaleY(p.y)}`).join(' ');
    body += `<path d="${d}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>`;
    pts.forEach(p => {
      body += `<circle cx="${scaleX(p.x)}" cy="${scaleY(p.y)}" r="3.5" fill="${color}" stroke="#fff" stroke-width="1.5"/>`;
    });
  });

  // Axes
  body += `<line x1="${ml}" y1="${mt}" x2="${ml}" y2="${mt + innerH}" stroke="#1a1a1a" stroke-width="1.5"/>`;
  body += `<line x1="${ml}" y1="${mt + innerH}" x2="${ml + innerW}" y2="${mt + innerH}" stroke="#1a1a1a" stroke-width="1.5"/>`;

  // Axis labels
  if (options.xLabel) body += `<text x="${ml + innerW / 2}" y="${H - 4}" text-anchor="middle" font-family="system-ui" font-size="12" fill="#6b6b6b">${_esc(options.xLabel)}</text>`;
  if (options.yLabel) body += `<text transform="rotate(-90)" x="${-(mt + innerH / 2)}" y="13" text-anchor="middle" font-family="system-ui" font-size="12" fill="#6b6b6b">${_esc(options.yLabel)}</text>`;

  // Legend for multi-series
  if (series.length > 1) {
    series.forEach((s, si) => {
      const color = s.color ?? DEFAULTS.colors[si % DEFAULTS.colors.length];
      const lx = ml + si * 120;
      body += `<rect x="${lx}" y="${mt - 16}" width="10" height="10" fill="${color}" rx="2"/>`;
      body += `<text x="${lx + 14}" y="${mt - 7}" font-family="system-ui" font-size="11" fill="#1a1a1a">${_esc(s.name)}</text>`;
    });
  }

  const title = options.title
    ? `<text x="${W / 2}" y="16" text-anchor="middle" font-family="system-ui" font-size="13" font-weight="700" fill="#1a1a1a">${_esc(options.title)}</text>`
    : '';

  container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;" role="img">${title}${body}</svg>`;
}

/**
 * Bubble chart.
 * @param {HTMLElement} container
 * @param {{x:number,y:number,r:number,label?:string,color?:string}[]} data
 * @param {{width?:number,height?:number,title?:string,xLabel?:string,yLabel?:string}} [options]
 */
function createBubbleChart(container, data, options = {}) {
  if (!data?.length) { container.innerHTML = '<p class="chart-caption">No data</p>'; return; }

  const W = options.width ?? DEFAULTS.width;
  const H = options.height ?? DEFAULTS.height;
  const ml = DEFAULTS.marginLeft;
  const mr = DEFAULTS.marginRight;
  const mt = options.title ? 36 : DEFAULTS.marginTop;
  const mb = DEFAULTS.marginBottom;
  const innerW = W - ml - mr;
  const innerH = H - mt - mb;

  const xTicks = _niceTicks(Math.min(...data.map(d => d.x)), Math.max(...data.map(d => d.x)));
  const yTicks = _niceTicks(Math.min(...data.map(d => d.y)), Math.max(...data.map(d => d.y)));
  const xMin = xTicks[0], xMax = xTicks.at(-1);
  const yMin = yTicks[0], yMax = yTicks.at(-1);
  const maxR = Math.max(...data.map(d => d.r));

  const scaleX = v => ml + ((v - xMin) / (xMax - xMin || 1)) * innerW;
  const scaleY = v => mt + innerH - ((v - yMin) / (yMax - yMin || 1)) * innerH;
  const scaleR = v => 4 + (v / (maxR || 1)) * 30;

  let body = '';

  yTicks.forEach(t => {
    const y = scaleY(t);
    body += `<line x1="${ml}" y1="${y}" x2="${ml + innerW}" y2="${y}" stroke="#e8e4dd" stroke-width="1"/>`;
    body += `<text x="${ml - 6}" y="${y}" text-anchor="end" dominant-baseline="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${fmt(t)}</text>`;
  });
  xTicks.forEach(t => {
    const x = scaleX(t);
    body += `<line x1="${x}" y1="${mt}" x2="${x}" y2="${mt + innerH}" stroke="#e8e4dd" stroke-width="1"/>`;
    body += `<text x="${x}" y="${mt + innerH + 14}" text-anchor="middle" font-family="system-ui" font-size="11" fill="#6b6b6b">${fmt(t)}</text>`;
  });

  // Sort by radius descending so small bubbles render on top
  [...data].sort((a, b) => b.r - a.r).forEach((d, i) => {
    const cx = scaleX(d.x), cy = scaleY(d.y), r = scaleR(d.r);
    const color = d.color ?? DEFAULTS.colors[i % DEFAULTS.colors.length];
    body += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" fill-opacity="0.7" stroke="${color}" stroke-width="1"/>`;
    if (d.label) {
      body += `<text x="${cx}" y="${cy + r + 12}" text-anchor="middle" font-family="system-ui" font-size="10" fill="#6b6b6b">${_esc(d.label)}</text>`;
    }
  });

  body += `<line x1="${ml}" y1="${mt}" x2="${ml}" y2="${mt + innerH}" stroke="#1a1a1a" stroke-width="1.5"/>`;
  body += `<line x1="${ml}" y1="${mt + innerH}" x2="${ml + innerW}" y2="${mt + innerH}" stroke="#1a1a1a" stroke-width="1.5"/>`;

  if (options.xLabel) body += `<text x="${ml + innerW / 2}" y="${H - 4}" text-anchor="middle" font-family="system-ui" font-size="12" fill="#6b6b6b">${_esc(options.xLabel)}</text>`;
  if (options.yLabel) body += `<text transform="rotate(-90)" x="${-(mt + innerH / 2)}" y="13" text-anchor="middle" font-family="system-ui" font-size="12" fill="#6b6b6b">${_esc(options.yLabel)}</text>`;

  const title = options.title
    ? `<text x="${W / 2}" y="16" text-anchor="middle" font-family="system-ui" font-size="13" font-weight="700" fill="#1a1a1a">${_esc(options.title)}</text>`
    : '';

  container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;" role="img">${title}${body}</svg>`;
}

/**
 * Heatmap with red→yellow→green color scale by default.
 * @param {HTMLElement} container
 * @param {{rows:string[], cols:string[], values:number[][]}} data
 * @param {{width?:number,height?:number,colorMin?:string,colorMid?:string,colorMax?:string,title?:string,format?:(v:number)=>string}} [options]
 */
function createHeatmap(container, data, options = {}) {
  if (!data?.rows?.length || !data?.cols?.length) {
    container.innerHTML = '<p class="chart-caption">No data</p>'; return;
  }

  const colorMin = options.colorMin ?? '#d64045';
  const colorMid = options.colorMid ?? '#f5c842';
  const colorMax = options.colorMax ?? '#2a9d5c';
  const format = options.format ?? (v => fmt(v, 1));

  const rowLabelW = Math.max(...data.rows.map(r => r.length)) * 7 + 8;
  const colLabelH = 36;
  const cellH = 32;
  const cellW = Math.max(40, Math.floor(
    ((options.width ?? DEFAULTS.width) - rowLabelW) / data.cols.length
  ));
  const W = rowLabelW + cellW * data.cols.length + 4;
  const H = colLabelH + cellH * data.rows.length + (options.title ? 28 : 4);
  const yOffset = options.title ? 24 : 0;

  const allVals = data.values.flat().filter(v => v != null && !isNaN(v));
  const minVal = Math.min(...allVals);
  const maxVal = Math.max(...allVals);
  const midVal = (minVal + maxVal) / 2;

  /** @param {number} v */
  const colorFor = v => {
    if (maxVal === minVal) return colorMid;
    const t = (v - minVal) / (maxVal - minVal);
    return t < 0.5
      ? lerpColor(colorMin, colorMid, t * 2)
      : lerpColor(colorMid, colorMax, (t - 0.5) * 2);
  };

  let body = '';

  if (options.title) {
    body += `<text x="${W / 2}" y="16" text-anchor="middle" font-family="system-ui" font-size="13" font-weight="700" fill="#1a1a1a">${_esc(options.title)}</text>`;
  }

  // Column headers
  data.cols.forEach((col, ci) => {
    const x = rowLabelW + ci * cellW + cellW / 2;
    body += `<text x="${x}" y="${yOffset + colLabelH - 8}" text-anchor="middle" font-family="system-ui" font-size="11" fill="#1a1a1a">${_esc(col)}</text>`;
  });

  // Cells
  data.rows.forEach((row, ri) => {
    const y = yOffset + colLabelH + ri * cellH;
    body += `<text x="${rowLabelW - 6}" y="${y + cellH / 2}" text-anchor="end" dominant-baseline="middle" font-family="system-ui" font-size="11" fill="#1a1a1a">${_esc(row)}</text>`;
    data.cols.forEach((_, ci) => {
      const v = data.values[ri]?.[ci];
      const x = rowLabelW + ci * cellW;
      const fill = (v != null && !isNaN(v)) ? colorFor(v) : '#eee';
      body += `<rect x="${x}" y="${y}" width="${cellW}" height="${cellH}" fill="${fill}" stroke="#fff" stroke-width="1.5"/>`;
      if (v != null && !isNaN(v)) {
        // Contrast: use white text on dark cells
        const [rr, gg, bb] = hexToRgb(fill.startsWith('rgb') ? '#888' : fill);
        const lum = (0.299 * rr + 0.587 * gg + 0.114 * bb) / 255;
        const textColor = lum < 0.5 ? '#fff' : '#1a1a1a';
        body += `<text x="${x + cellW / 2}" y="${y + cellH / 2}" text-anchor="middle" dominant-baseline="middle" font-family="system-ui" font-size="11" fill="${textColor}">${_esc(format(v))}</text>`;
      }
    });
  });

  container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;" role="img">${body}</svg>`;
}

// === ANIMATED COUNTER ===

/**
 * Count up from 0 to target over duration ms when element enters viewport.
 * @param {HTMLElement} el
 * @param {number} target
 * @param {number} [duration]
 * @param {string} [suffix]
 */
function animateCount(el, target, duration = 1200, suffix = '') {
  const start = performance.now();
  const step = ts => {
    const t = Math.min((ts - start) / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = fmt(Math.round(eased * target)) + suffix;
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// === SCROLL-TRIGGERED ANIMATIONS ===

/** Add .visible to .scroll-fade elements when they enter the viewport */
function initScrollAnimations() {
  const els = document.querySelectorAll('.scroll-fade');
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  els.forEach(el => io.observe(el));
}

// === INIT ALL ===

function initAll() {
  initTooltips();
  initPopups();
  initScrollAnimations();

  // Animated counters — trigger once element is visible
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = /** @type {HTMLElement} */ (entry.target);
      const target = parseFloat(el.dataset.count ?? '0');
      const duration = parseInt(el.dataset.duration ?? '1200', 10);
      const suffix = el.dataset.suffix ?? '';
      animateCount(el, target, duration, suffix);
      counterObserver.unobserve(el);
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('[data-count]').forEach(el => counterObserver.observe(el));
}

export { initAll, initTooltips, initPopups, initScrollAnimations, animateCount, lerpColor, fmt, createBarChart, createLineChart, createBubbleChart, createHeatmap };
