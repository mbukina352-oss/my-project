// Печатает HTML-слайды из build/ в PDF (список в build/jobs.json, его пишет make_deck.py)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const build = path.join(__dirname, 'build');
  const jobs = JSON.parse(fs.readFileSync(path.join(build, 'jobs.json'), 'utf8'));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [src, pdf] of jobs) {
    await page.goto('file://' + path.join(build, src), { waitUntil: 'networkidle' });
    await page.pdf({ path: path.join(__dirname, pdf), width: '1920px', height: '1080px', printBackground: true });
    console.log(pdf);
  }
  await browser.close();
})();
