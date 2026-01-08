// Simple copy script to bring demo.html into mobile/www as index.html
// Run via `npm run prepare:web`

const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const demoSrc = path.join(repoRoot, 'demo.html');
const wwwDir = path.join(__dirname, '..', 'www');
const indexDst = path.join(wwwDir, 'index.html');
const vendorDir = path.join(wwwDir, 'vendor');
const xlsxLocal = path.join(vendorDir, 'xlsx.min.js');
const xlsxCdn = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.min.js';

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function replaceCdnWithLocal(html) {
  // Replace CDN XLSX script with local vendor copy
  return html.replace(
    /<script\s+src=["']https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/xlsx\/0\.18\.5\/xlsx\.min\.js["']><\/script>/,
    '<script src="vendor/xlsx.min.js"></script>'
  );
}

function adjustDemoHtml(html, useLocalXlsx) {
  // Inject a top bar with "Open Full Platform" using Capacitor Browser when available
  const inject = `\n<div style="position:sticky;top:0;background:#333;color:#fff;padding:10px 16px;z-index:9999;display:flex;justify-content:space-between;align-items:center;">\n  <div>📱 Finance Diagnostics (Mobile)</div>\n  <div style=\"display:flex;gap:8px;\">\n    <button id=\"openSettings\" style=\"background:#444;color:#fff;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;\">Settings</button>\n    <button id=\"openFullPlatform\" style=\"background:#667eea;color:#fff;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;\">Open Full Platform</button>\n  </div>\n</div>\n<div id=\"settingsPanel\" style=\"display:none;padding:10px 16px;border-bottom:1px solid #ddd;background:#fafafa;\">\n  <label style=\"display:block;margin-bottom:6px;\">Full Platform URL</label>\n  <input id=\"platformUrlInput\" type=\"url\" placeholder=\"https://your-app.onrender.com\" style=\"width:100%;padding:8px;border:1px solid #ccc;border-radius:6px;\" />\n  <div style=\"margin-top:8px;display:flex;gap:8px;\">\n    <button id=\"savePlatformUrl\" style=\"background:#667eea;color:#fff;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;\">Save</button>\n    <button id=\"closeSettings\" style=\"background:#e0e0e0;color:#333;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;\">Close</button>\n  </div>\n</div>\n`;

  const withBar = html.replace('<body>', '<body>' + inject);

  // Append script to handle opening the hosted site and settings panel
  const script = `\n<script type=\"module\">\n  import { Browser } from 'https://cdn.skypack.dev/@capacitor/browser';\n  const btn = document.getElementById('openFullPlatform');\n  const openSettings = document.getElementById('openSettings');\n  const closeSettings = document.getElementById('closeSettings');\n  const savePlatformUrl = document.getElementById('savePlatformUrl');\n  const settingsPanel = document.getElementById('settingsPanel');\n  const input = document.getElementById('platformUrlInput');\n\n  function currentUrl() {\n    return localStorage.getItem('FULL_PLATFORM_URL') || 'https://YOUR-RENDER-APP-URL';\n  }\n  input.value = currentUrl();\n\n  openSettings?.addEventListener('click', () => { settingsPanel.style.display = 'block'; });\n  closeSettings?.addEventListener('click', () => { settingsPanel.style.display = 'none'; });\n  savePlatformUrl?.addEventListener('click', () => {\n    if (input.value) { localStorage.setItem('FULL_PLATFORM_URL', input.value); }\n    settingsPanel.style.display = 'none';\n  });\n\n  btn?.addEventListener('click', async () => {\n    try {\n      const TARGET_URL = currentUrl();\n      if (Browser && Browser.open) {\n        await Browser.open({ url: TARGET_URL });\n      } else {\n        window.open(TARGET_URL, '_blank');\n      }\n    } catch (e) {\n      console.error(e);\n      window.open(currentUrl(), '_blank');\n    }\n  });\n</script>\n`;
  // Replace CDN XLSX reference with local vendor file when available
  const finalHtml = useLocalXlsx ? replaceCdnWithLocal(withBar) : withBar;
  return finalHtml.replace('</body>', script + '\n</body>');
}

(async function main() {
  ensureDir(wwwDir);
  ensureDir(vendorDir);
  if (!fs.existsSync(demoSrc)) {
    console.error('demo.html not found at repo root');
    process.exit(1);
  }
  // Ensure local XLSX copy exists; fetch from CDN if missing (best-effort)
  let haveLocalXlsx = fs.existsSync(xlsxLocal);
  if (!haveLocalXlsx) {
    console.log('Downloading XLSX from CDN to vendor...');
    const https = require('https');
    const file = fs.createWriteStream(xlsxLocal);
    const done = new Promise((resolve, reject) => {
      https.get(xlsxCdn, (res) => {
        if (res.statusCode !== 200) {
          reject(new Error('Failed to download XLSX: ' + res.statusCode));
          return;
        }
        res.pipe(file);
        file.on('finish', () => file.close(resolve));
      }).on('error', reject);
    });
    try {
      require('child_process');
    } catch (_) {}
    try {
      await done;
      haveLocalXlsx = true;
      console.log('XLSX saved to', xlsxLocal);
    } catch (e) {
      console.warn('Could not download XLSX', e);
    }
  }

  const html = fs.readFileSync(demoSrc, 'utf8');
  const out = adjustDemoHtml(html, haveLocalXlsx);
  fs.writeFileSync(indexDst, out);
  console.log('Copied demo.html to mobile/www/index.html with top bar. Local XLSX:', haveLocalXlsx);
})();
