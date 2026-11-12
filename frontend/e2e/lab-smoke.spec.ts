import { test, expect } from '@playwright/test';

test('başlangıç ekranı gerçek API kataloğunu ve simülasyonu yükler', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Ateşböceği Algoritması/i })).toBeVisible();
  const healthResponse = await page.request.get('/api/health');
  expect(healthResponse.ok()).toBeTruthy();
  const health = await healthResponse.json();
  await expect(page.locator('.build-version')).toHaveText(`BUILD ${health.version}`);
  await expect(page.getByRole('button', { name: /Parçacık Sürü Optimizasyonu/i })).toBeVisible();
  await expect(page.getByText('FONKSİYON DEĞERLENDİRME')).toBeVisible();
  await expect(page.getByText('Katalog yükleniyor...')).toHaveCount(0);
});

test('yedi laboratuvar arasında gezilebilir', async ({ page }) => {
  await page.goto('/');
  const sections = [
    ['Karşılaştırma Laboratuvarı', 'Algoritma Karşılaştırma Laboratuvarı'],
    ['Benchmark Stüdyosu', 'Çoklu Benchmark Stüdyosu'],
    ['Parametre Duyarlılığı', 'Parametre Duyarlılığı Laboratuvarı'],
    ['Yüksek Boyut Laboratuvarı', 'Yüksek Boyutlu Optimizasyon Laboratuvarı'],
    ['Akademik Raporlar', 'Akademik Deney Raporları'],
    ['Bilimsel Doğrulama', 'Bilimsel Doğrulama ve Performans'],
    ['Deney Kuyruğu', 'Kalıcı Deney Görev Kuyruğu'],
  ];
  for (const [buttonName, title] of sections) {
    await page.getByRole('navigation', { name: 'Birincil gezinme' })
      .getByRole('button', { name: buttonName }).click();
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
    // Arşiv başlığı yalnızca Akademik Raporlar sekmesinde bulunur.
    // Kuyruk sayfasında aynı başlığı aramak yanlış-negatif test üretir.
    if (buttonName === 'Akademik Raporlar') {
      await expect(page.getByRole('heading', { name: 'Deney arşivi', exact: true })).toBeVisible();
    }
    if (buttonName === 'Deney Kuyruğu') {
      await expect(page.getByRole('heading', { name: 'Görevler', exact: true })).toBeVisible();
    }
  }
});

test('algoritma filtresi ve seçim işlemi çalışır', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Algoritma ara' }).fill('diferansiyel');
  await expect(page.getByRole('button', { name: /Diferansiyel Evrim/i })).toBeVisible();
  await page.getByRole('button', { name: /Diferansiyel Evrim/i }).click();
  await expect(page.getByRole('heading', { name: /Diferansiyel Evrim/i })).toBeVisible();
});

test('API hatalı isteği reddeder, katalog 15 algoritma döndürür', async ({ request }) => {
  const catalog = await request.get('/api/catalog');
  expect(catalog.ok()).toBeTruthy();
  expect((await catalog.json()).algorithms).toHaveLength(15);
  const invalid = await request.post('/api/simulations', { data: { iterations: -1 } });
  expect(invalid.status()).toBe(422);
});


test('kalıcı görev kuyruğunda deney çalışır ve sonuç arşive kaydedilir', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('navigation', {name:'Birincil gezinme'})
    .getByRole('button', {name:'Deney Kuyruğu'}).click();
  await page.getByLabel('Popülasyon').fill('8');
  await page.getByLabel('İterasyon').fill('5');
  await page.getByLabel('Tekrar / tohum').fill('2');
  await page.getByRole('button', {name:'Deneyi kuyruğa ekle'}).click();
  await expect(page.getByText('Seçilen görev')).toBeVisible();
  await expect(page.getByRole('button', {name:'Arşiv sonucunu aç'})).toBeVisible({timeout:30000});
  await page.getByRole('button', {name:'Arşiv sonucunu aç'}).click();
  await expect(page.getByRole('heading', {name:'Arşivlenmiş deney'})).toBeVisible();
});

test('çoklu benchmark arka plan görevi arşivlenir', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('navigation', {name:'Birincil gezinme'})
    .getByRole('button', {name:'Deney Kuyruğu'}).click();
  await page.getByLabel('Deney türü').selectOption('benchmark');
  await page.getByLabel('Popülasyon').fill('8');
  await page.getByLabel('İterasyon').fill('1');
  await page.getByLabel('Tekrar / tohum').fill('2');
  await page.getByRole('button', {name:'Deneyi kuyruğa ekle'}).click();
  await expect(page.getByRole('button',{name:'Arşiv sonucunu aç'})).toBeVisible({timeout:30000});
  await page.getByRole('button',{name:'Arşiv sonucunu aç'}).click();
  await expect(page.getByRole('heading', {name:'Arşivlenmiş deney'})).toBeVisible();
  await expect(page.getByText(/2 amaç fonksiyonu/)).toBeVisible();
});

test('OFAT duyarlılık görevi arşivlenir', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('navigation', {name:'Birincil gezinme'})
    .getByRole('button', {name:'Deney Kuyruğu'}).click();
  await page.getByLabel('Deney türü').selectOption('sensitivity');
  await expect(page.getByLabel('İncelenen parametre').locator('option')).not.toHaveCount(0);
  await page.getByLabel('Popülasyon').fill('8');
  await page.getByLabel('İterasyon').fill('1');
  await page.getByLabel('Tekrar / tohum').fill('2');
  await page.getByRole('button', {name:'Deneyi kuyruğa ekle'}).click();
  await expect(page.getByRole('button',{name:'Arşiv sonucunu aç'})).toBeVisible({timeout:30000});
  await page.getByRole('button',{name:'Arşiv sonucunu aç'}).click();
  await expect(page.getByRole('heading', {name:'Arşivlenmiş deney'})).toBeVisible();
  await expect(page.locator('.jobs-result > p').first()).toContainText('pso_inertia_weight');
});

test('görev olayları görünür ve geçmiş silme akademik arşivi korur', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('navigation', { name: 'Birincil gezinme' })
    .getByRole('button', { name: 'Deney Kuyruğu' }).click();
  await page.getByLabel('Popülasyon').fill('8');
  await page.getByLabel('İterasyon').fill('5');
  await page.getByLabel('Tekrar / tohum').fill('2');
  await page.getByRole('button', { name: 'Deneyi kuyruğa ekle' }).click();
  await expect(page.getByRole('button', { name: 'Arşiv sonucunu aç' })).toBeVisible({timeout:30000});
  await expect(page.getByRole('heading', {name: 'Görev olay geçmişi'})).toBeVisible();
  await expect(page.getByText('Deney tamamlandı ve arşive kaydedildi.')).toBeVisible();

  const response = await page.request.get('/api/jobs');
  expect(response.ok()).toBeTruthy();
  const { jobs } = await response.json();
  const jobId = jobs[0].id as string;
  expect(jobs[0].state).toBe('completed');
  expect(jobs[0].checkpoint_units).toBe(0); // archived results supersede temporary snapshots
  expect(jobs[0].reused_units).toBe(0); // no restart was required during this test
  const stored = await page.request.get(`/api/dimensional/${jobId}`);
  expect(stored.ok()).toBeTruthy();

  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', {name: 'Görev geçmişini kaldır'}).click();
  await expect(page.getByRole('heading', {name:'Seçilen görev'})).toHaveCount(0);
  expect((await page.request.get(`/api/jobs/${jobId}`)).status()).toBe(404);
  expect((await page.request.get(`/api/dimensional/${jobId}`)).ok()).toBeTruthy();
});


test('bilimsel doğrulama kaydedilmiş 5D deneyi yeniden hesaplamadan denetler', async ({page}) => {
  const created = await page.request.post('/api/dimensional', {data:{
    algorithms:['pso','gwo'],objective:'sphere',dimensions:5,
    population_size:8,iterations:5,trials:2,seed_start:420,
  }});
  expect(created.ok()).toBeTruthy();
  const {experiment_id} = await created.json();
  await page.goto('/');
  await page.getByRole('navigation', {name:'Birincil gezinme'})
    .getByRole('button', {name:'Bilimsel Doğrulama'}).click();
  await page.getByRole('button', {name:/SPHERE · 5D/}).first().click();
  await expect(page.getByText('Arşiv tutarlılığı doğrulandı')).toBeVisible();
  await expect(page.getByRole('heading', {name:'Kalite ve ölçülmüş süreler'})).toBeVisible();
  const audit = await page.request.get(`/api/science/dimensional/${experiment_id}`);
  expect(audit.ok()).toBeTruthy();
  const data = await audit.json();
  expect(data.status).toBe('passed');
  expect(data.expected_total_evaluations).toBe(192);
});


test('kısa ekran yüksekliğinde algoritma filtresi ve navigasyon tıklanabilir kalır', async ({ page }) => {
  await page.setViewportSize({width: 1280, height: 600});
  await page.goto('/');
  const sidebar = page.locator('.sidebar');
  // The two independently scrollable regions remain usable at laptop heights.
  expect(await sidebar.locator('.primary-nav').evaluate(el => el.clientHeight)).toBeGreaterThanOrEqual(92);
  expect(await sidebar.locator('.algorithm-scroll').evaluate(el => el.clientHeight)).toBeGreaterThanOrEqual(120);
  // Exercise both scroll regions with real pointer clicks, not force:true.
  await page.getByRole('navigation', {name: 'Birincil gezinme'})
    .getByRole('button', {name: 'Son Deneyler'}).click();
  await expect(page.getByRole('heading', {name: 'Deney Kayıtları'})).toBeVisible();
  await page.getByRole('textbox', {name: 'Algoritma ara'}).fill('diferansiyel');
  await page.getByRole('button', {name: /Diferansiyel Evrim/i}).click();
  await expect(page.getByRole('heading', {name: /Diferansiyel Evrim/i})).toBeVisible();
});


test('mobil menü klavyeyle kapanır ve odağı menü düğmesine döndürür', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 740 });
  await page.goto('/');
  const open = page.getByRole('button', { name: 'Menüyü aç' });
  await open.click();
  await expect(open).toHaveAttribute('aria-expanded', 'true');
  await expect(page.getByRole('button', { name: 'Menüyü kapat' }).first()).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(open).toHaveAttribute('aria-expanded', 'false');
  await expect(open).toBeFocused();
  await open.click();
  await page.getByRole('navigation', { name: 'Birincil gezinme' })
    .getByRole('button', { name: 'Bilimsel Doğrulama' }).click();
  await expect(page.getByRole('heading', { name: 'Bilimsel Doğrulama ve Performans' })).toBeVisible();
  await expect(open).toHaveAttribute('aria-expanded', 'false');
});

test('yalnızca açılan laboratuvar yüklenir ve ana içerik klavyeden erişilir', async ({ page }) => {
  const chunks: string[] = [];
  page.on('response', response => {
    if (response.url().includes('/src/components/')) chunks.push(response.url());
  });
  await page.goto('/');
  await expect(page.getByRole('heading', {name: /Ateşböceği Algoritması/i})).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Ana içeriğe geç' })).toBeFocused();
  await page.getByRole('navigation',{name:'Birincil gezinme'})
    .getByRole('button',{name:'Parametre Duyarlılığı'}).click();
  await expect(page.getByRole('heading',{name:'Parametre Duyarlılığı Laboratuvarı'})).toBeVisible();
  await expect(page.locator('.sens-layout')).toBeVisible();
  expect(chunks.some(path => path.includes('SensitivityLab'))).toBe(true);
});
