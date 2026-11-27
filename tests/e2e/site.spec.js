const { test, expect } = require('@playwright/test');

test('portada conserva navegación, un producto real y layout desktop', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/');
  await expect(page).toHaveTitle(/Miura/);
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Tu infraestructura');
  await expect(page.locator('.app-card')).toHaveCount(1);
  await expect(page.getByRole('navigation').getByRole('link', { name: 'Miura Panel' })).toHaveAttribute('href', '/panel/');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: testInfo.outputPath('site-desktop.png'), fullPage: true });
});

test('página Panel muestra la descarga oficial del manifest y capturas cargadas', async ({ page }, testInfo) => {
  await page.goto('/panel/');
  const download = page.getByRole('link', { name: /Descargar versión estable/ }).first();
  await expect(download).toHaveAttribute('href', /^https:\/\/github\.com\/juanramonvf\/miura-panel\/releases\/download\/v\d+\.\d+\.\d+\//);
  await expect(page.locator('.hash')).toHaveText(/^[a-f0-9]{64}$/);
  const screenshots = page.locator('figure img');
  await expect(screenshots).toHaveCount(2);
  for (const image of await screenshots.all()) {
    await expect(image).toHaveJSProperty('complete', true);
    expect(await image.evaluate((element) => element.naturalWidth)).toBeGreaterThan(0);
  }
  await page.screenshot({ path: testInfo.outputPath('panel-desktop.png'), fullPage: true });
});

test('layout móvil no desborda y la navegación sigue accesible', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const route of ['/', '/panel/', '/help/', '/news/']) {
    await page.goto(route);
    await expect(page.getByRole('navigation')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `desbordamiento en ${route}`).toBeTruthy();
  }
  await page.goto('/panel/');
  await page.screenshot({ path: testInfo.outputPath('site-mobile.png'), fullPage: true });
});

test('legacy aliases mantienen su ruta y su fragmento', async ({ page }) => {
  await page.goto('/help.html#ssh');
  await expect(page).toHaveURL(/\/help\/#ssh$/);
  await expect(page.locator('#ssh')).toBeVisible();
  await page.goto('/novedades.html');
  await expect(page).toHaveURL(/\/news\/$/);
  await expect(page.getByRole('heading', { name: 'Novedades' })).toBeVisible();
});
