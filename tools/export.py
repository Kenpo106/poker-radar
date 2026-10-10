#!/usr/bin/env python3
"""Convert an ArtifactData out_dir export into data/*.json for the public site.

Usage: python3 tools/export.py <export dir with events/ venues/ settings/> [repo root]
"""
import sys, json, pathlib, datetime
src = pathlib.Path(sys.argv[1]); root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else '.')
out = root / 'data'; out.mkdir(exist_ok=True)

def docs(name):
    d = src / name
    return [dict(id=p.stem, **json.loads(p.read_text(encoding='utf-8'))) for p in sorted(d.glob('*.json'))] if d.exists() else []

events = docs('events')
venues = [v for v in docs('venues') if not v.get('removed')]
settings = next((s for s in docs('settings') if s['id'] == 'main'), None)
if settings: settings.pop('id', None)
if len(events) < 5: sys.exit('refusing to publish: only %d events in export' % len(events))

def dump(name, obj):
    (out / f'{name}.json').write_text(json.dumps(obj, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
dump('events', events); dump('venues', venues); dump('settings', settings or {})
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='minutes')
dump('meta', {'updated': now, 'events': len(events), 'venues': len(venues)})
print(f'events={len(events)} venues={len(venues)} updated={now}')
