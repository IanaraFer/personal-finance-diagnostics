// Simple copy script to bring demo.html into mobile/www as index.html
// Run via `npm run prepare:web`

const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const demoSrc = path.join(repoRoot, 'demo.html');
const wwwDir = path.join(__dirname, '..', 'www');
const indexDst = path.join(wwwDir, 'index.html');

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function adjustDemoHtml(html) {
  // Inject a top bar with "Open Full Platform" using Capacitor Browser when available
  const inject = `\n<div style="position:sticky;top:0;background:#333;color:#fff;padding:10px 16px;z-index:9999;display:flex;justify-content:space-between;align-items:center;">\n  <div>📱 Finance Diagnostics (Mobile)</div>\n  <button id="openFullPlatform" style="background:#667eea;color:#fff;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;">Open Full Platform</button>\n</div>\n`;

  const withBar = html.replace('<body>', '<body>' + inject);

  // Append script to handle opening the hosted site
  const script = `\n<script type="module">\n  import { Browser } from 'https://cdn.skypack.dev/@capacitor/browser';\n  const btn = document.getElementById('openFullPlatform');\n  const TARGET_URL = localStorage.getItem('FULL_PLATFORM_URL') || 'https://YOUR-RENDER-APP-URL';\n  btn?.addEventListener('click', async () => {\n    try {\n      if (Browser && Browser.open) {\n        await Browser.open({ url: TARGET_URL });\n      } else {\n        window.open(TARGET_URL, '_blank');\n      }\n    } catch (e) {\n      console.error(e);\n      window.open(TARGET_URL, '_blank');\n    }\n  });\n</script>\n`;
  return withBar.replace('</body>', script + '\n</body>');
}

(function main() {
  ensureDir(wwwDir);
  if (!fs.existsSync(demoSrc)) {
    console.error('demo.html not found at repo root');
    process.exit(1);
  }
  const html = fs.readFileSync(demoSrc, 'utf8');
  const out = adjustDemoHtml(html);
  fs.writeFileSync(indexDst, out);
  console.log('Copied demo.html to mobile/www/index.html with top bar.');
})();
