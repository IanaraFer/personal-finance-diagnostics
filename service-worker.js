/* Simple PWA Service Worker for offline support */
const CACHE_NAME = 'finance-diag-cache-v2';
const CORE_ASSETS = [
  '/',
  '/demo',
  '/static/manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((k) => (k === CACHE_NAME ? null : caches.delete(k)))))
  );
  self.clients.claim();
});

function isStatic(reqUrl) {
  try {
    const url = new URL(reqUrl);
    return url.origin === location.origin && url.pathname.startsWith('/static/');
  } catch (_) {
    return false;
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Avoid interfering with Stripe or POSTs
  if (request.method !== 'GET' || /stripe/i.test(request.url)) {
    return; // let network handle
  }

  // Navigation requests: network-first with cache fallback
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/'))
    );
    return;
  }

  // Static assets: cache-first
  if (isStatic(request.url)) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request).then((resp) => {
        const respClone = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, respClone));
        return resp;
      }))
    );
    return;
  }
});
