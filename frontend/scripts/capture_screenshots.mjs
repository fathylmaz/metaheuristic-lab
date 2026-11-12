/** Take real screenshots from a user-run local instance; never fake UI imagery. */
import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const target = path.join(root, 'docs', 'screenshots');
const base = process.env.METAHEURISTIC_SCREENSHOT_BASE || 'http://127.0.0.1:5173';
await mkdir(target, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const cases = [
  { filename: 'simulation.png', menu: null, heading: /Ateşböceği Algoritması/i },
  { filename: 'comparison.png', menu: 'Karşılaştırma Laboratuvarı', heading: 'Algoritma Karşılaştırma Laboratuvarı' },
  { filename: 'benchmark.png', menu: 'Benchmark Stüdyosu', heading: 'Çoklu Benchmark Stüdyosu' },
  { filename: 'dimensional.png', menu: 'Yüksek Boyut Laboratuvarı', heading: 'Yüksek Boyutlu Optimizasyon Laboratuvarı' },
  { filename: 'reports.png', menu: 'Akademik Raporlar', heading: 'Akademik Deney Raporları' },
  { filename: 'science.png', menu: 'Bilimsel Doğrulama', heading: 'Bilimsel Doğrulama ve Performans' },
  { filename: 'jobs.png', menu: 'Deney Kuyruğu', heading: 'Kalıcı Deney Görev Kuyruğu' },
];
try {
  const response = await page.goto(base, { waitUntil: 'domcontentloaded', timeout: 20000 });
  if (!response?.ok()) throw new Error(`Frontend reachable but HTTP ${response?.status()}`);
  for (const item of cases) {
    if (item.menu) {
      await page.getByRole('navigation', { name: 'Birincil gezinme' })
        .getByRole('button', { name: item.menu, exact: true }).click();
    }
    await page.getByRole('heading', { name: item.heading }).waitFor({ state: 'visible', timeout: 30000 });
    await page.screenshot({ path: path.join(target, item.filename), fullPage: false, animations: 'disabled' });
    console.log(`Captured: docs/screenshots/${item.filename}`);
  }
  console.log('REVIEW ALL SCREENSHOTS BEFORE ANY PUBLIC COMMIT (local/private records may be visible).');
} finally {
  await browser.close();
}
