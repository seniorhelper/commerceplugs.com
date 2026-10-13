#!/usr/bin/env python3
"""Build a relative-path copy of the site for hosting under a sub-path.

The production site lives at the domain root, so every link is written as
"/stores/" etc. A preview served from a nested URL needs those rewritten to
"../stores/". This script does that, and nothing else, into preview/.
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, "preview")
COPY = ["assets", "feeds", ".well-known", "c", "t", "b", "stores", "search",
        "contents", "for-brands", "pricing", "how-it-works", "join", "about",
        "contact", "advertise", "faq", "journal", "favicon.ico", "site.webmanifest",
        "index.html", "404.html", "search-index.json", "llms.txt", "sitemap.xml",
        "robots.txt"]

def depth_prefix(rel):
    d = rel.count(os.sep)
    return "../" * d if d else ""

def relativise(html, prefix):
    """Rewrite root-absolute hrefs/srcs to paths relative to this page."""
    def sub(m):
        attr, path = m.group(1), m.group(2)
        tail = path[1:]
        # peel off fragment then query so they survive the index.html rewrite
        frag = ""
        if "#" in tail:
            tail, f = tail.split("#", 1); frag = "#" + f
        query = ""
        if "?" in tail:
            tail, q = tail.split("?", 1); query = "?" + q
        # directory URLs need an explicit index.html when served as plain files
        if tail == "" or tail.endswith("/"):
            tail += "index.html"
        return f'{attr}="{prefix}{tail}{query}{frag}"'
    return re.sub(r'\b(href|src)="(/[^"]*)"', sub, html)

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

for item in COPY:
    src = os.path.join(ROOT, item)
    if not os.path.exists(src):
        print("skip (missing):", item); continue
    dst = os.path.join(OUT, item)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)

n = 0
for dirpath, _, files in os.walk(OUT):
    for f in files:
        if not f.endswith(".html"):
            continue
        full = os.path.join(dirpath, f)
        rel  = os.path.relpath(full, OUT)
        pre  = depth_prefix(rel)
        html = open(full, encoding="utf-8").read()
        html = relativise(html, pre)
        # tell app.js where the search index is from this depth
        html = html.replace("<script src=", f'<script>window.CP_INDEX="{pre}search-index.json"</script>\n<script src=', 1)
        open(full, "w", encoding="utf-8").write(html)
        n += 1
print(f"preview built: {n} pages rewritten -> {OUT}")
