#!/usr/bin/env python3
"""Generate the raster brand assets: favicons, app icons and Open Graph cards.

Run from the project root:  python3 tools/make_assets.py
Writes into assets/icons/ and assets/og/. The TTFs under tools/fonts are used
for rendering only and are never served.
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(ROOT, "assets/icons")
OG   = os.path.join(ROOT, "assets/og")
F    = os.path.join(ROOT, "tools/fonts")
os.makedirs(ICON, exist_ok=True); os.makedirs(OG, exist_ok=True)

INK      = (22, 24, 28)
PAPER    = (247, 246, 241)
OXBLOOD  = (140, 29, 24)
PETROL   = (29, 77, 67)
MUTED    = (154, 149, 139)

def font(name, size):
    return ImageFont.truetype(os.path.join(F, name), size)

def center(d, box, text, fnt, fill):
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), text, font=fnt)
    d.text((x0 + (x1 - x0 - (r - l)) / 2 - l, y0 + (y1 - y0 - (b - t)) / 2 - t), text, font=fnt, fill=fill)

# ---------------------------------------------------------------- mark
def mark(size, bleed=True):
    """Oxblood plate, cream serif CP, with a rule under it like a printed stamp."""
    s = size * 4                       # supersample, then downscale
    im = Image.new("RGBA", (s, s), OXBLOOD + (255,))
    d = ImageDraw.Draw(im)
    if not bleed:                      # maskable/app icon keeps a safe margin
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, s, s], fill=OXBLOOD)
    fnt = font("Newsreader.ttf", int(s * 0.52))
    center(d, (0, int(-s * 0.04), s, int(s * 0.92)), "CP", fnt, PAPER)
    # the rule: a printer's mark, and it reads as a bar even at 16px
    d.rectangle([int(s * 0.22), int(s * 0.80), int(s * 0.78), int(s * 0.855)], fill=PAPER)
    return im.resize((size, size), Image.LANCZOS)

for n in (16, 32, 48, 180, 192, 512):
    mark(n).convert("RGB").save(os.path.join(ICON, f"icon-{n}.png"))
mark(180).convert("RGB").save(os.path.join(ICON, "apple-touch-icon.png"))
ims = [mark(n).convert("RGB") for n in (16, 32, 48)]
ims[0].save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)], append_images=ims[1:])

# an SVG mark too: sharp at any size, and it is what modern browsers prefer
open(os.path.join(ICON, "icon.svg"), "w").write(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" fill="#8C1D18"/>'
    '<text x="32" y="43" text-anchor="middle" fill="#F7F6F1" '
    'font-family="Newsreader,Times New Roman,Georgia,serif" font-weight="600" font-size="33">CP</text>'
    '<rect x="14" y="51" width="36" height="3.5" fill="#F7F6F1"/></svg>')

# ---------------------------------------------------------------- og cards
W, H = 1200, 630

def wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def price(v):
    """Never round a price up: a card that says "from $20" when the listing is
    $19.99 is a small lie, and this site's whole argument is that it does not
    tell those."""
    return f"${v:,.2f}".rstrip("0").rstrip(".") if v < 100 else f"${v:,.0f}"

def og(path, kicker, title, facts, accent=OXBLOOD):
    im = Image.new("RGB", (W, H), PAPER)
    d  = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 10], fill=accent)                       # head rule
    d.rectangle([64, 96, W - 64, 99], fill=INK)                   # scotch rule
    d.rectangle([64, 103, W - 64, 104], fill=INK)

    d.text((64, 52), kicker.upper(), font=font("Archivo.ttf", 23), fill=accent)

    size = 86 if len(title) < 26 else (68 if len(title) < 46 else 54)
    fnt  = font("Newsreader.ttf", size)
    lines = wrap(d, title, fnt, W - 128)[:3]
    y = 150
    for ln in lines:
        d.text((64, y), ln, font=fnt, fill=INK); y += int(size * 1.12)

    if facts:
        fy = H - 150
        d.rectangle([64, fy - 34, W - 64, fy - 33], fill=(207, 203, 192))
        x = 64
        for k, v in facts[:4]:
            d.text((x, fy), str(v), font=font("Newsreader.ttf", 46), fill=PETROL)
            d.text((x, fy + 60), k, font=font("Newsreader-reg.ttf", 25), fill=(119, 125, 133))
            x += 285

    d.rectangle([0, H - 56, W, H], fill=INK)
    d.text((64, H - 44), "commerceplugs.com", font=font("Archivo.ttf", 25), fill=PAPER)
    d.text((W - 64 - d.textlength("The index of independent stores", font=font("Archivo.ttf", 25)), H - 44),
           "The index of independent stores", font=font("Archivo.ttf", 25), fill=(154, 149, 139))
    im.save(path, quality=88, optimize=True)
    return path

D = os.path.join(ROOT, "data")
site   = json.load(open(os.path.join(D, "site.json")))
cats   = json.load(open(os.path.join(D, "categories.json")))
stores = json.load(open(os.path.join(D, "stores.json")))
prods  = json.load(open(os.path.join(D, "products.json")))
slug = lambda t: re.sub(r"[^a-z0-9]+", "-", str(t).lower()).strip("-") or "other"

n = 0
og(os.path.join(OG, "default.jpg"), "Independent stores", "Buy it from the people who make it.",
   [("stores", len(stores)), ("listings", len(prods)), ("categories", len(cats)), ("commission", "0%")]); n += 1

for s in stores:
    ps = [p for p in prods if p["store"] == s["slug"]]
    pr = sorted(float(p["price"]) for p in ps if p.get("price"))
    og(os.path.join(OG, f"store-{s['slug']}.jpg"), "Independent store", s["name"],
       [("listings", len(ps)),
        ("types", len({p.get("subcategory") for p in ps if p.get("subcategory")})),
        ("from", f"${pr[0]:,.0f}" if pr else "—"),
        ("to", f"${pr[-1]:,.0f}" if pr else "—")]); n += 1

for c in cats:
    ps = [p for p in prods if p.get("category") == c["slug"]]
    og(os.path.join(OG, f"cat-{c['slug']}.jpg"), "Category", c["name"],
       [("listings", len(ps)), ("stores", len({p["store"] for p in ps}))] if ps else []); n += 1

for key, items in [("type", "subcategory"), ("brand", "brand")]:
    groups = {}
    for p in prods:
        if p.get(items): groups.setdefault(slug(p[items]), []).append(p)
    for k, ps in groups.items():
        pr = sorted(float(p["price"]) for p in ps if p.get("price"))
        og(os.path.join(OG, f"{key}-{k}.jpg"), key.title(), ps[0][items],
           [("listings", len(ps)), ("from", f"${pr[0]:,.0f}" if pr else "—"),
            ("to", f"${pr[-1]:,.0f}" if pr else "—")]); n += 1

print(f"icons + {n} Open Graph cards written")
