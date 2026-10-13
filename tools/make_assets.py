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

INK      = (14, 14, 17)
PAPER    = (255, 255, 255)
OXBLOOD  = (241, 90, 34)      # orange: the primary, on fills and the mark
PETROL   = (110, 59, 255)     # violet: the secondary, on figures and data
MUTED    = (95, 95, 105)

def font(name, size):
    return ImageFont.truetype(os.path.join(F, name), size)

def center(d, box, text, fnt, fill):
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), text, font=fnt)
    d.text((x0 + (x1 - x0 - (r - l)) / 2 - l, y0 + (y1 - y0 - (b - t)) / 2 - t), text, font=fnt, fill=fill)

# ---------------------------------------------------------------- mark
def mark(size, bleed=True):
    """Orange tile, white plug: a body with square shoulders and a rounded chin,
    plus two prongs. Proportions matter more than detail — the body has to stay
    small enough that the prongs still read as prongs at 16px."""
    s = size * 8                       # supersample, then downscale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = s / 64.0
    def b(*v): return [x * u for x in v]

    d.rounded_rectangle(b(1, 1, 63, 63), radius=int(16 * u), fill=OXBLOOD)

    # body: 24 wide, 19 tall, sitting high so the prongs have room
    bx0, bx1, by0, by1 = 20.0, 44.0, 13.0, 32.0
    d.rounded_rectangle(b(bx0, by0, bx1, by1), radius=int(3 * u), fill=PAPER)
    d.rounded_rectangle(b(bx0, by0 + 7, bx1, by1), radius=int(9 * u), fill=PAPER)

    # prongs: long enough to be unmistakable, thick enough to survive 16px
    pw = 7.0 if size < 48 else 6.2
    gap = 8.0
    for x in (32 - gap / 2 - pw, 32 + gap / 2):
        d.rounded_rectangle(b(x, 33.5, x + pw, 51), radius=int(pw / 2 * u), fill=PAPER)

    return im.resize((size, size), Image.LANCZOS)

for n in (16, 32, 48, 180, 192, 512):
    mark(n).convert("RGB").save(os.path.join(ICON, f"icon-{n}.png"))
mark(180).convert("RGB").save(os.path.join(ICON, "apple-touch-icon.png"))
ims = [mark(n).convert("RGB") for n in (16, 32, 48)]
ims[0].save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)], append_images=ims[1:])

# an SVG mark too: sharp at any size, and it is what modern browsers prefer
open(os.path.join(ICON, "icon.svg"), "w").write(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect x="2" y="2" width="60" height="60" rx="16" fill="#F15A22"/>'
    '<path d="M23 13h18a3 3 0 0 1 3 3v7a9 9 0 0 1-9 9h-6a9 9 0 0 1-9-9v-7a3 3 0 0 1 3-3z" fill="#fff"/>'
    '<rect x="24.2" y="33.5" width="6.2" height="17.5" rx="3.1" fill="#fff"/>'
    '<rect x="33.6" y="33.5" width="6.2" height="17.5" rx="3.1" fill="#fff"/></svg>')

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
    d.rectangle([0, 0, 12, H], fill=accent)                        # spine
    im.paste(mark(56), (64, 48), mark(56))                         # the icon
    d.text((136, 62), kicker.upper(), font=font("Body.ttf", 23), fill=PETROL)
    d.rectangle([64, 124, W - 64, 125], fill=(227, 227, 231)) 

    size = 86 if len(title) < 26 else (68 if len(title) < 46 else 54)
    fnt  = font("Display.ttf", size)
    lines = wrap(d, title, fnt, W - 128)[:3]
    y = 164
    for ln in lines:
        d.text((64, y), ln, font=fnt, fill=INK); y += int(size * 1.12)

    if facts:
        fy = H - 150
        d.rectangle([64, fy - 34, W - 64, fy - 33], fill=(227, 227, 231))
        x = 64
        for k, v in facts[:4]:
            d.text((x, fy), str(v), font=font("Display.ttf", 46), fill=PETROL)
            d.text((x, fy + 60), k, font=font("Body.ttf", 25), fill=MUTED)
            x += 285

    d.rectangle([0, H - 56, W, H], fill=INK)
    d.text((64, H - 44), "commerceplugs.com", font=font("Body.ttf", 25), fill=PAPER)
    d.text((W - 64 - d.textlength("The index of independent stores", font=font("Body.ttf", 25)), H - 44),
           "The index of independent stores", font=font("Body.ttf", 25), fill=(142, 142, 154))
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
