// 网络优先（3 秒超时回退缓存）：在线时拿最新版本，弱网/离线用缓存。只缓存成功的响应。改版本号即可让旧缓存失效。
const V = 'observer-v6';
const FILES = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-192.png',
  './data/words.json', './data/recite.json', './data/books.json', './data/pinyin.json'];
self.addEventListener('install', e => { e.waitUntil(caches.open(V).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;   // GitHub API 同步请求不走缓存
  const net = fetch(e.request).then(r => { if (r.ok) { const cp = r.clone(); caches.open(V).then(c => c.put(e.request, cp)); } return r; });
  const timeout = new Promise(res => setTimeout(res, 3000));
  e.respondWith(Promise.race([net, timeout]).then(r => r || caches.match(e.request, {ignoreSearch: true}).then(c => c || net))
    .catch(() => caches.match(e.request, {ignoreSearch: true}).then(r => r || caches.match('./index.html'))));
});
