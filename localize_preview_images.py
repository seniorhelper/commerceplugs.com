#!/usr/bin/env python3
"""Preview-only: fetch product thumbnails locally so the hosted preview can show
them. The live site keeps pointing at the store's own CDN — we do not rehost a
merchant's images in production."""
import json, os, re, io, urllib.request, hashlib, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(ROOT, "preview")
IMGD = os.path.join(PREV, "img")
os.makedirs(IMGD, exist_ok=True)

prods = json.load(open(os.path.join(ROOT, "data/products.json")))
mapping, failed = {}, 0
for p in prods:
    src = p.get("image")
    if not src: continue
    # Shopify serves a resized copy on request; 220px is plenty for a 74px thumb
    url = src + ("&" if "?" in src else "?") + "width=220"
    name = hashlib.sha1(src.encode()).hexdigest()[:16] + ".jpg"
    dest = os.path.join(IMGD, name)
    if not os.path.exists(dest):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (preview thumbnailer)"})
            with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
                f.write(r.read())
        except Exception as ex:
            failed += 1
            print("  miss:", ex, file=sys.stderr)
            continue
    mapping[src] = name

n = 0
for dirpath, _, files in os.walk(PREV):
    for f in files:
        if not f.endswith((".html", ".json")): continue
        full = os.path.join(dirpath, f)
        depth = os.path.relpath(full, PREV).count(os.sep)
        pre = "../" * depth
        html = io.open(full, encoding="utf-8").read()
        before = html
        for src, name in mapping.items():
            html = html.replace(src, pre + "img/" + name)
        if html != before:
            io.open(full, "w", encoding="utf-8").write(html)
            n += 1

total = sum(os.path.getsize(os.path.join(IMGD, x)) for x in os.listdir(IMGD))
print(f"localized {len(mapping)} images ({total/1024:.0f} KB) across {n} files, {failed} failed")
