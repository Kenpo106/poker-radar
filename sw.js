// Network-first for everything; cached copy only when offline.
const CACHE = 'poker-radar-v1';
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(fetch(req).then(res => {
    const copy = res.clone();
    caches.open(CACHE).then(c => c.put(req.url.split('?')[0], copy));
    return res;
  }).catch(() => caches.match(req.url.split('?')[0])));
});
