// Прави narachnik.pdf от narachnik.html.  node make_pdf.js <папка-с-изрязани-снимки> <изход.pdf> <данни.json>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [imgDir, out, dataFile] = process.argv.slice(2);
  const d = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
  let html = fs.readFileSync(path.join(__dirname, 'narachnik.html'), 'utf8');
  for (const [k, v] of Object.entries(d.text)) html = html.split('{{' + k + '}}').join(v);
  for (const [id, f] of Object.entries(d.img)) html = html.split('{{img' + id + '}}').join('file://' + path.resolve(imgDir, f));
  const tmp = path.join(path.dirname(path.resolve(out)), '_narachnik.html');
  fs.writeFileSync(tmp, html);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + tmp, { waitUntil: 'networkidle' });
  await p.pdf({ path: out, format: 'A5', printBackground: true });
  await b.close(); fs.unlinkSync(tmp);
})();
