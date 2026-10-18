const V = "jec-v1";
const PRE = ["/hors-ligne/", "/static/css/legacy.css", "/static/css/site.css", "/static/css/assistant.css", "/static/images/logo.png",
             "/static/vendor/bootstrap-icons/bootstrap-icons.min.css"];
self.addEventListener("install", e => { e.waitUntil(caches.open(V).then(c => c.addAll(PRE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== V).map(x => caches.delete(x)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET" || u.origin !== location.origin || /^\/(admin|gestion|assistant|comptes)/.test(u.pathname)) return;
  if (r.mode === "navigate") { e.respondWith(fetch(r).catch(() => caches.match("/hors-ligne/"))); return; }
  if (u.pathname.startsWith("/static/") || u.pathname.startsWith("/media/")) {
    e.respondWith(caches.match(r).then(hit => {
      const net = fetch(r).then(res => { const cp = res.clone(); caches.open(V).then(c => c.put(r, cp)); return res; }).catch(() => hit);
      return hit || net;
    }));
  }
});
