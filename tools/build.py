#!/usr/bin/env python3
"""Build the public (no-login) site from the Claude artifact page.

Usage: python3 tools/build.py <artifact index.html> [repo root]
Wraps the artifact page in a full HTML document, adds PWA tags and a small
shim that serves window.claude.use('db') from the static JSON files in data/.
"""
import sys, pathlib, re

src = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
# Accept either the raw artifact source or the wrapped page returned by Artifact read.
k = src.find('<title>')
if k < 0: sys.exit('not an app page: no <title>')
src = src[k:]
src = re.sub(r'</body>\s*</html>\s*$', '', src.rstrip())
if 'class="wrap"' not in src or '<script>' not in src: sys.exit('not an app page')
root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else '.')

HEAD = '''<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="台灣撲克協會錦標賽一次看：手續費、保底人數、預估 ROI 與今日推薦。">
<meta name="theme-color" content="#0A0A0B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="撲克雷達">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
'''

SHIM = r'''<script>
/* Public build: read-only data from data/*.json instead of the Claude artifact database. */
(function(){
  const listeners = [];
  const cache = {};
  async function load(name){
    const r = await fetch('data/' + name + '.json?t=' + Math.floor(Date.now()/60000), { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }
  function snapOf(arr){ return { docs: arr.map(d => ({ id: d.id, data: () => { const o = { ...d }; delete o.id; return o; } })) }; }
  async function refresh(){
    for (const l of listeners){
      try {
        const data = await load(l.name);
        const key = JSON.stringify(data);
        if (cache[l.key] === key) continue;
        cache[l.key] = key;
        l.cb(l.kind === 'col' ? snapOf(data) : { exists: !!data, data: () => data || {} });
      } catch(e){ if (l.err) l.err(e); }
    }
  }
  const ro = () => Promise.reject(new Error('公開版不能修改資料'));
  const db = {
    collection(name){ return {
      onSnapshot(cb, err){ listeners.push({ kind:'col', name, key:'c:'+name, cb, err }); refresh(); return () => {}; },
      doc(){ return { update: ro, set: ro, delete: ro }; }
    }; },
    doc(path){ const name = path.split('/')[0]; return {
      onSnapshot(cb, err){ listeners.push({ kind:'doc', name, key:'d:'+path, cb, err }); refresh(); return () => {}; },
      update: ro, set: ro
    }; }
  };
  window.claude = { use: async (k) => k === 'db' ? db : k === 'user' ? { canEdit: async () => false } : null };
  setInterval(refresh, 10*60*1000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(()=>{}));
})();
</script>
'''

# split the artifact page: leading <title>/<link>/<style> go into <head>, the rest into <body>
i = src.index('<style>')
j = src.index('</style>') + len('</style>')
head_extra = src[:j]
body = src[j:]
body = body.replace('這個檢視讀不到資料庫，請登入 claude.ai 後開啟。', '暫時讀不到資料，請稍後重新整理。')
first_script = body.index('<script>')
body = body[:first_script] + SHIM + body[first_script:]

out = HEAD + head_extra + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n'
(root / 'index.html').write_text(out, encoding='utf-8')
print('wrote', root / 'index.html', len(out), 'bytes')
