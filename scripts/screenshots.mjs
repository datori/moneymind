/**
 * Automated screenshot generator for the Finance Dashboard.
 *
 * Usage:
 *   node scripts/screenshots.mjs
 *
 * Requires:
 *   - Finance installed in .venv: pip install -e .
 *   - Demo database: python -m finance.demo.seed (if data/demo.db missing)
 *   - Playwright + Chromium: npx playwright install chromium
 *
 * Output: screenshots/{dashboard,spending,transactions,recurring,accounts}-demo.png
 */

import { chromium } from 'playwright';
import { spawn } from 'child_process';
import { writeFileSync, readFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const OUT  = join(ROOT, 'screenshots');
const PORT = 8746;
const BASE = `http://127.0.0.1:${PORT}`;

// ─── Server ──────────────────────────────────────────────────────────────────

function startServer() {
  // Finance uses system Python (no venv) — installed with pip3 install -e .
  const proc = spawn(
    'python3',
    ['-c', `import sys; sys.argv=['x','--host','127.0.0.1','--port','${PORT}']; from finance.web.app import main; main()`],
    { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] }
  );
  proc.stdout.on('data', () => {}); // drain to prevent blocking
  proc.stderr.on('data', () => {}); // drain to prevent blocking
  proc.on('error', (e) => { throw e; });
  return proc;
}

async function waitForServer(maxMs = 20000) {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${BASE}/`);
      if (res.status < 500) return;
    } catch {}
    await new Promise(r => setTimeout(r, 400));
  }
  throw new Error(`Server did not respond within ${maxMs}ms`);
}

// ─── Polish wrapper ───────────────────────────────────────────────────────────

async function polish(browser, rawPngPath, label) {
  const rawB64 = readFileSync(rawPngPath).toString('base64');

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 48px;
    min-height: 100vh;
  }
  .frame {
    border-radius: 10px;
    overflow: hidden;
    box-shadow:
      0 0 0 1px rgba(255,255,255,0.08),
      0 8px 32px rgba(0,0,0,0.6),
      0 32px 80px rgba(0,0,0,0.4);
    max-width: 100%;
  }
  img { display: block; max-width: 100%; }
  .label {
    position: fixed;
    bottom: 16px;
    right: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 11px;
    color: rgba(255,255,255,0.2);
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>
  <div class="frame">
    <img src="data:image/png;base64,${rawB64}" />
  </div>
  <span class="label">${label}</span>
</body>
</html>`;

  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle' });
  const box = await page.locator('.frame').boundingBox();
  await page.setViewportSize({
    width:  Math.round(box.x * 2 + box.width  + 96),
    height: Math.round(box.y * 2 + box.height + 96),
  });
  const buf = await page.screenshot({ fullPage: true });
  await page.close();
  return buf;
}

// ─── Capture one page ─────────────────────────────────────────────────────────

async function capture(browser, path, label, { width = 1400, height = 900, params = {} } = {}) {
  const page = await browser.newPage();
  await page.setViewportSize({ width, height });
  const qs = new URLSearchParams({ demo: '1', ...params }).toString();
  await page.goto(`${BASE}${path}?${qs}`, { waitUntil: 'networkidle' });
  // Extra wait for Chart.js animations to settle
  await page.waitForTimeout(800);
  const rawPath = join(OUT, `_raw_${label}.png`);
  await page.screenshot({ path: rawPath, fullPage: false });
  await page.close();
  return rawPath;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('Starting finance-dashboard (demo mode)…');
  const server = startServer();
  await waitForServer();
  console.log('Server ready.');

  const browser = await chromium.launch();
  mkdirSync(OUT, { recursive: true });

  // Feb 2026 is a full seeded month — far richer than the partial current month
  const FEB = { start: '2026-02-01', end: '2026-02-28' };

  const shots = [
    { route: '/',             label: 'dashboard',    outFile: 'dashboard-demo.png',    title: 'Finance · Dashboard'    },
    { route: '/spending',     label: 'spending',     outFile: 'spending-demo.png',     title: 'Finance · Spending',     params: FEB },
    { route: '/transactions', label: 'transactions', outFile: 'transactions-demo.png', title: 'Finance · Transactions', params: FEB },
    { route: '/recurring',    label: 'recurring',    outFile: 'recurring-demo.png',    title: 'Finance · Recurring'    },
    { route: '/accounts',     label: 'accounts',     outFile: 'accounts-demo.png',     title: 'Finance · Accounts'     },
  ];

  try {
    for (const { route, label, outFile, title, params } of shots) {
      console.log(`Capturing ${label}…`);
      const rawPath = await capture(browser, route, label, { params });
      const polished = await polish(browser, rawPath, title);
      writeFileSync(join(OUT, outFile), polished);
      console.log(`  ✓ ${outFile}`);
    }
  } finally {
    await browser.close();
    server.kill();
  }

  console.log('\nScreenshots saved to screenshots/');
  for (const { outFile } of shots) console.log(`  ${outFile}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
