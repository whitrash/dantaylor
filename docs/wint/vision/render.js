// Uso: node render.js <dir-de-trabajo> <salida.pdf> [captura-ancho.png] [captura-telefono.png] [captura-oscuro.png]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [dir, outPdf, shotWide, shotPhone, shotDark] = process.argv.slice(2);
  const body = fs.readFileSync(path.join(dir, 'que-es-wint.html'), 'utf8')
    .replace(/<link rel="preconnect"[^>]*>\n?/g, '')
    .replace(/<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>/, '<link rel="stylesheet" href="fonts/local.css">');
  const html = '<!doctype html><html lang="es"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body style="margin:0">' +
    body + '</body></html>';
  const tmp = path.join(dir, '_render.html');
  fs.writeFileSync(tmp, html);

  const browser = await chromium.launch();
  const url = 'file://' + tmp;

  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);
  if (shotWide) await page.screenshot({ path: shotWide, fullPage: true });
  await page.pdf({ path: outPdf, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;font-size:7.5pt;color:#596178;padding:0 15mm;display:flex;justify-content:space-between;font-family:sans-serif"><span>Wint · informe de visión · 8 de octubre de 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>' });

  if (shotPhone) {
    const p2 = await browser.newPage({ viewport: { width: 400, height: 860 }, colorScheme: 'light' });
    await p2.goto(url);
    await p2.evaluate(() => document.fonts.ready);
    const sw = await p2.evaluate(() => document.documentElement.scrollWidth);
    console.log('phone scrollWidth', sw);
    await p2.screenshot({ path: shotPhone, fullPage: true });
  }
  if (shotDark) {
    const p3 = await browser.newPage({ viewport: { width: 1280, height: 900 }, colorScheme: 'dark' });
    await p3.goto(url);
    await p3.evaluate(() => document.fonts.ready);
    await p3.screenshot({ path: shotDark, fullPage: false });
  }
  await browser.close();
})();
