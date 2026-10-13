#!/usr/bin/env python3
"""Commerce Plugs static site generator.

Reads data/*.json and emits the whole site as static HTML.
No dependencies. Run:  python3 build.py
"""
import json, os, re, shutil, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
D = lambda p: os.path.join(ROOT, p)
TODAY = datetime.date.today().isoformat()

SITE = json.load(open(D("data/site.json")))
CATS = json.load(open(D("data/categories.json")))
STORES = json.load(open(D("data/stores.json")))
PRODUCTS = json.load(open(D("data/products.json")))
JOURNAL  = sorted(json.load(open(D("data/journal.json"))), key=lambda x: x["date"], reverse=True)

BASE = "https://" + SITE["domain"]
BRAND = SITE["brand"]
CATBY = {c["slug"]: c for c in CATS}
STOREBY = {s["slug"]: s for s in STORES}
for c in CATS:
    c["stores"] = [s for s in STORES if c["slug"] in s.get("categories", [])]
    c["products"] = [p for p in PRODUCTS if p.get("category") == c["slug"]]

def slug(t):
    out = re.sub(r"[^a-z0-9]+", "-", str(t).lower()).strip("-")
    return out or "other"

# A directory is only as good as the ways into it. Beyond the 16 editorial
# categories we index every product type and every brand carried, so a shopper
# or a crawler can enter at "cold plunge tub" or "Bestbath" rather than only at
# "Home & Bath".
TYPES, BRANDS = {}, {}
for p in PRODUCTS:
    if p.get("subcategory"):
        TYPES.setdefault(slug(p["subcategory"]), {"name": p["subcategory"], "items": []})["items"].append(p)
    if p.get("brand"):
        BRANDS.setdefault(slug(p["brand"]), {"name": p["brand"], "items": []})["items"].append(p)
TYPES  = dict(sorted(TYPES.items(),  key=lambda kv: (-len(kv[1]["items"]), kv[1]["name"])))
BRANDS = dict(sorted(BRANDS.items(), key=lambda kv: (-len(kv[1]["items"]), kv[1]["name"])))

e = lambda t: html.escape(str(t if t is not None else ""), quote=True)
# Line icons drawn on a 24x24 grid, 1.6 stroke, currentColor. Inline so they
# cost no request and inherit the brand colour in both themes.
PATHS = {
 "bath":   '<path d="M3 13h18v2a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4v-2Z"/><path d="M6 13V6.5A2.5 2.5 0 0 1 10.5 5"/><path d="M6 19v2M18 19v2"/>',
 "kitchen":'<rect x="4" y="9" width="16" height="10" rx="1.5"/><path d="M2 9h20M9.5 5.5h5"/>',
 "chip":   '<rect x="7" y="7" width="10" height="10" rx="1"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/>',
 "shirt":  '<path d="M9 3 4 6l2 4 2-1v12h8V9l2 1 2-4-5-3a3 3 0 0 1-6 0Z"/>',
 "drop":   '<path d="M12 3c4 5 6 7.6 6 10a6 6 0 0 1-12 0c0-2.4 2-5 6-10Z"/>',
 "leaf":   '<path d="M20 4c0 9-5 15-13 15H5v-2C5 10 11 4 20 4Z"/><path d="m5 20 15-16"/>',
 "paw":    '<circle cx="7" cy="9" r="2"/><circle cx="12" cy="6.8" r="2"/><circle cx="17" cy="9" r="2"/><path d="M12 12.5c3 0 5 2 5 4.3S14.5 20.5 12 20.5s-5-1.4-5-3.7 2-4.3 5-4.3Z"/>',
 "dice":   '<rect x="4" y="4" width="16" height="16" rx="2"/><circle cx="9" cy="9" r="1.2"/><circle cx="15" cy="9" r="1.2"/><circle cx="9" cy="15" r="1.2"/><circle cx="15" cy="15" r="1.2"/>',
 "bolt":   '<path d="M13 3 5 14h6l-1 7 8-11h-6l1-7Z"/>',
 "pen":    '<path d="m4 20 1-4L16 5l3 3L8 19l-4 1Z"/><path d="m14 7 3 3"/>',
 "wrench": '<path d="M20.5 5.5a5 5 0 0 1-6.9 6.9L6 20l-2-2 7.6-7.6a5 5 0 0 1 6.9-6.9l-3 3 2 2 3-3Z"/>',
 "cup":    '<path d="M4 7h12v7a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V7Z"/><path d="M16 9h2a2.5 2.5 0 0 1 0 5h-2"/><path d="M4 21h13"/>',
 "gem":    '<path d="m12 4 7 5-7 11L5 9l7-5Z"/><path d="M5 9h14M12 4 9 9l3 11M12 4l3 5-3 11"/>',
 "frame":  '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="m6 17 4-5 3 3 2-2 3 4"/><circle cx="9" cy="9" r="1.3"/>',
 "star":   '<path d="m12 3 2.6 6.1 6.4.9-5 4.2L17.5 21 12 17.5 6.5 21 8 14.2 3 10l6.4-.9L12 3Z"/>',
 "car":    '<path d="M4 13 6 8h12l2 5"/><rect x="3" y="13" width="18" height="4" rx="1"/><circle cx="7.5" cy="17.5" r="1.7"/><circle cx="16.5" cy="17.5" r="1.7"/>',
}
def icon(key):
    d = PATHS.get(key) or PATHS["chip"]
    return ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
            'focusable="false">' + d + "</svg>")

def write(path, body):
    full = D(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(body)
    return path

def money(p):
    try: return "$" + f"{float(p):,.2f}"
    except Exception: return "$" + str(p)

# ---------------------------------------------------------------- chrome
ORG = {"@context":"https://schema.org","@type":"Organization","@id":BASE+"/#org",
       "name":BRAND,"url":BASE+"/","description":SITE["pitch"],
       "logo":{"@type":"ImageObject","url":BASE+"/assets/icons/icon-512.png","width":512,"height":512},
       "image":BASE+"/assets/og/default.jpg",
       "founder":{"@type":"Organization","name":SITE["publisher"],"url":SITE["publisher_url"]},
       "foundingDate":str(SITE["founded"]),
       "knowsAbout":["independent retail","ecommerce directories","product data","machine-readable commerce"],
       "contactPoint":{"@type":"ContactPoint","contactType":"customer support",
                       "url":BASE+"/contact/","availableLanguage":"English"}}

def head(title, desc, path, extra="", ld=None, og="default", og_alt=None):
    url = BASE + path
    blocks = ""
    ld = ([ld] if isinstance(ld, dict) else list(ld or [])) + [ORG]
    if ld:
        for obj in (ld if isinstance(ld, list) else [ld]):
            blocks += '<script type="application/ld+json">%s</script>\n' % json.dumps(obj, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#6E3BFF">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/assets/icons/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:site_name" content="{e(BRAND)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{BASE}/assets/og/{og}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(og_alt or title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{BASE}/assets/og/{og}.jpg">
<link rel="preload" href="/assets/fonts/Outfit-400-5.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/BricolageGrotesque-700-2.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/app.js" defer></script>
<link rel="alternate" type="application/json" href="{BASE}/feeds/products.json" title="Product feed">
<link rel="alternate" type="application/rss+xml" href="{BASE}/journal/feed.xml" title="{e(BRAND)} Journal">
<link rel="sitemap" type="application/xml" href="{BASE}/sitemap.xml">
{blocks}{extra}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""

# The mark is the out-arrow: every link on this site leaves for the seller.
# Settled in the brand round — orange tile, white arrow, 16px radius.
def arrow_svg(size=39, fill="#6E3BFF", glyph="#fff", rx=16):
    return (f'<svg viewBox="0 0 64 64" width="{size}" height="{size}" aria-hidden="true" focusable="false">'
            f'<rect x="2" y="2" width="60" height="60" rx="{rx}" fill="{fill}"/>'
            f'<path d="M24 40 L40 24" stroke="{glyph}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M27 24 H40 V37" fill="none" stroke="{glyph}" stroke-width="6" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg>')

# The plug is a CONTENT icon, not the logo. It appears only where the page is
# literally talking about plugging a store or an app in.
def plug_svg(size=24, color="currentColor"):
    return (f'<svg class="glyph" viewBox="0 0 64 64" width="{size}" height="{size}" '
            'aria-hidden="true" focusable="false">'
            f'<path d="M23 13h18a3 3 0 0 1 3 3v7a9 9 0 0 1-9 9h-6a9 9 0 0 1-9-9v-7a3 3 0 0 1 3-3z" fill="{color}"/>'
            f'<rect x="24.2" y="33.5" width="6.2" height="17.5" rx="3.1" fill="{color}"/>'
            f'<rect x="33.6" y="33.5" width="6.2" height="17.5" rx="3.1" fill="{color}"/></svg>')

# A socket, for the other half of the metaphor: this is what you plug into.
def socket_svg(size=24, color="currentColor"):
    return (f'<svg class="glyph" viewBox="0 0 64 64" width="{size}" height="{size}" '
            'aria-hidden="true" focusable="false">'
            f'<rect x="8" y="8" width="48" height="48" rx="12" fill="none" stroke="{color}" stroke-width="5"/>'
            f'<rect x="24" y="22" width="6" height="20" rx="3" fill="{color}"/>'
            f'<rect x="34" y="22" width="6" height="20" rx="3" fill="{color}"/></svg>')

MARK = arrow_svg()   # 39px: 30% up on the old 30px

def wordmark():
    return f'{MARK}<span class="m1">commerce<b>plugs</b><i>.</i></span>'

def header(active=None):
    opts = '<option value="">All categories</option>' + "".join(
        f'<option value="{c["slug"]}">{e(c["name"])}</option>' for c in CATS)
    strip = "".join(
        f'<a href="/c/{c["slug"]}/"{" aria-current=\"page\"" if active==c["slug"] else ""}>{e(c["name"])}</a>'
        for c in CATS)
    return f"""<header class="top">
<div class="top-in">
  <a class="mark" href="/" aria-label="{e(BRAND)} home">{wordmark()}</a>
  <form class="find" action="/search/" method="get" role="search">
    <label class="sr" for="q">Search independent stores and products</label>
    <select name="c" aria-label="Category">{opts}</select>
    <input id="q" name="q" type="search" placeholder="Search products from independent stores" autocomplete="off">
    <button type="submit">Search</button>
  </form>
  <nav class="top-act" aria-label="Account">
    <a class="no-sm" href="/contents/">Contents</a>\n    <a class="no-sm" href="/stores/">Stores</a>
    <a class="no-sm" href="/how-it-works/">How it works</a>
    <a class="cta" href="/join/">Plug in your store</a>
  </nav>
</div>
</header>
<nav class="strip" aria-label="Categories"><div class="strip-in">
<a href="/stores/">All stores</a>{strip}
</div></nav>
"""

def footer():
    cols = ""
    for group, links in [
        ("Shop", [("Contents","/contents/"),("All stores","/stores/"),("Search","/search/"),("Recently added","/stores/")]),
        ("For brands", [("Why list here","/for-brands/"),("Pricing","/pricing/"),("How it works","/how-it-works/"),("Advertise","/advertise/"),("Plug in your store","/join/")]),
        ("Machine", [("Store feed","/feeds/stores.json"),("Product feed","/feeds/products.json"),("MCP server","/.well-known/mcp/server.json"),("llms.txt","/llms.txt")]),
        ("Company", [("About","/about/"),("Journal","/journal/"),("Questions","/faq/"),("Contact","/contact/"),("Advertise","/advertise/"),("Publisher",SITE["publisher_url"])]),
    ]:
        items = "".join(f'<li><a href="{l}">{e(n)}</a></li>' for n, l in links)
        cols += f'<div><h4>{e(group)}</h4><ul>{items}</ul></div>'
    return f"""<footer class="foot">
<div class="foot-in">
  <div class="foot-cols">
    <div>
      <a class="mark" href="/" style="margin-bottom:10px" aria-label="{e(BRAND)} home">{wordmark()}</a>
      <p class="sm muted" style="max-width:34ch">{e(SITE["pitch"])}</p>
      <p class="rail"><b>Index built</b> {TODAY}<span class="dot"></span><b>Stores</b> {len(STORES)}<span class="dot"></span><b>Listings</b> {len(PRODUCTS)}</p>
    </div>
    {cols}
  </div>
  <div class="foot-end">
    <span>© {SITE["founded"] if str(SITE["founded"])==TODAY[:4] else str(SITE["founded"])+"–"+TODAY[:4]} {e(BRAND)} · Published by {e(SITE["publisher"])}</span>
    <span>Every listing links to the brand's own store. We never take the transaction.</span>
  </div>
</div>
</footer>
</body>
</html>"""

def crumbs(trail):
    out = []
    for i, (name, link) in enumerate(trail):
        if i: out.append("<span>/</span>")
        out.append(f'<a href="{link}">{e(name)}</a>' if link else f"<span>{e(name)}</span>")
    return '<nav class="crumb wrap" aria-label="Breadcrumb">' + "".join(out) + "</nav>"

def ld_crumbs(trail):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":n,**({"item":BASE+l} if l else {})}
        for i,(n,l) in enumerate(trail)]}

# ---------------------------------------------------------------- partials
def host(url):
    return re.sub(r"^https?://(www\.)?", "", str(url)).rstrip("/")

def status_tag(s):
    if s.get("verified"):
        return f'<span class="tag tag-ok">Verified {e(s["verified"])}</span>'
    return '<span class="tag tag-open">Pending verification</span>'

def catalog_tag(s):
    if s.get("catalog_status") == "connected":
        return '<span class="tag tag-ok">Catalog connected</span>'
    return '<span class="tag">Catalog not connected</span>'

def money_mono(v):
    try: return f"${float(v):,.2f}"
    except Exception: return "$" + str(v)

def listing_row(p):
    """One line of a trade price list. No card, no float, no radius."""
    s = STOREBY.get(p["store"], {})
    img = (f'<img src="{e(p["image"])}" alt="" loading="lazy" decoding="async">'
           if p.get("image") else f'<span class="sm muted">{e((p.get("sku") or "")[:6])}</span>')
    bits = []
    if p.get("brand"): bits.append(f'<a href="/b/{slug(p["brand"])}/"><b>{e(p["brand"])}</b></a>')
    if p.get("subcategory"): bits.append(f'<a href="/t/{slug(p["subcategory"])}/">{e(p["subcategory"])}</a>')
    if p.get("dimensions"): bits.append(e(p["dimensions"]))
    if p.get("finish"): bits.append(e(p["finish"]))
    bits.append("in stock" if p.get("availability") == "in_stock" else e(p.get("availability", "")))
    if p.get("sku"): bits.append(e(p["sku"]))
    meta = '<span class="sep">·</span>'.join(bits)
    desc = f'<p class="desc">{e(p["blurb"])}</p>' if p.get("blurb") else ""
    return f"""<div class="row">
  <span class="th">{img}</span>
  <div>
    <a class="ttl" href="{e(p["url"])}" rel="nofollow noopener" target="_blank">{e(p["title"])}</a>
    <p class="meta">{meta}</p>
    {desc}
  </div>
  <div class="amt">
    <span class="p">{money_mono(p["price"])}</span>
    <a class="go" href="{e(p["url"])}" rel="nofollow noopener" target="_blank">{e(s.get("name", "store"))} \u2192</a>
  </div>
</div>"""

def plate(p, n=None):
    """A product reproduced large on white stock. The shop half of the page."""
    img = (f'<img src="{e(p["image"])}" alt="{e(p["title"])}" loading="lazy" decoding="async">'
           if p.get("image") else "")
    spec = " \u00b7 ".join(x for x in [p.get("brand"), p.get("dimensions") or p.get("finish") or p.get("subcategory")] if x)
    num = f'<span class="no">{n:02d}</span>' if n else ""
    return f"""<a class="plate" href="{e(p["url"])}" rel="nofollow noopener" target="_blank">
  {num}<span class="fig">{img}</span>
  <span class="cap">
    <span class="t">{e(p["title"])}</span>
    <span class="m">{e(spec)}</span>
    <span class="p">{money_mono(p["price"])}</span>
  </span>
</a>"""

def views_switch():
    return ('<span class="views" role="group" aria-label="View">'
            '<button type="button" data-view="plates" aria-pressed="true">Plates</button>'
            '<button type="button" data-view="rows" aria-pressed="false">List</button></span>')

def catalog(items, start_grid=True):
    """Both views, server-rendered. The switch only toggles hidden."""
    if not items: return ""
    return (f'<div class="plates" data-view-pane="plates"{"" if start_grid else " hidden"}>'
            + "".join(plate(x, i+1) for i, x in enumerate(items)) + "</div>"
            + f'<div class="rows" data-view-pane="rows"{" hidden" if start_grid else ""}>'
            + "".join(listing_row(x) for x in items) + "</div>")

def index_entry(name, href, count, unit=""):
    return (f'<a class="ix" href="{href}"><span class="nm">{e(name)}</span>'
            f'<span class="lead"></span><span class="ct">{count}{unit}</span></a>')

def register_row(i, s):
    cats = ", ".join(CATBY[c]["name"] for c in s.get("categories", []) if c in CATBY)
    n = len([x for x in PRODUCTS if x["store"] == s["slug"]])
    state = (f'verified {e(s["verified"])}' if s.get("verified") else "pending verification")
    return f"""<tr>
  <td class="ix-n">{i:02d}</td>
  <td class="nm"><a href="/stores/{e(s["slug"])}/">{e(s["name"])}</a>
    <span class="dom">{e(host(s["url"]))}</span></td>
  <td>{e(cats)}</td>
  <td>{e(", ".join(s.get("ships_to", [])) or "\u2014")}</td>
  <td class="num">{n}</td>
  <td class="num"><span class="rail">{state}</span></td>
</tr>"""

def product_card(p):
    s = STOREBY.get(p["store"], {})
    return f"""<article class="card card-hover prod">
  <div class="shot"><span class="ph">{e(p.get("sku",""))}</span></div>
  <h3><a href="{e(p["url"])}" rel="nofollow noopener" target="_blank">{e(p["title"])}</a></h3>
  <p class="from">from <a href="/stores/{e(p["store"])}/">{e(s.get("name",p["store"]))}</a></p>
  <p class="price">{money(p["price"])} <span>{e(p.get("currency","USD"))}</span></p>
  <p class="rail"><b>{"In stock" if p.get("availability")=="in_stock" else e(p.get("availability",""))}</b><span class="dot"></span>{e(p.get("subcategory",""))}</p>
  <a class="btn btn-sm btn-brand mt2" href="{e(p["url"])}" rel="nofollow noopener" target="_blank">Buy at {e(s.get("name",""))}</a>
</article>"""

def store_card(s):
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z0-9]+", s["name"])[:2]).upper()
    cats = " · ".join(CATBY[c]["name"] for c in s.get("categories", []) if c in CATBY)
    n = len([p for p in PRODUCTS if p["store"] == s["slug"]])
    return f"""<article class="card card-hover store">
  <div class="store-top">
    <div class="store-logo">{e(initials)}</div>
    <div>
      <h3><a href="/stores/{e(s["slug"])}/">{e(s["name"])}</a></h3>
      <p class="bl">{e(s.get("tagline") or host(s["url"]))}</p>
    </div>
  </div>
  <p class="rail"><b>{e(cats)}</b></p>
  <div class="store-foot">
    <span class="rail">{status_tag(s)}</span>
    <span class="rail">{n} listing{"s" if n!=1 else ""}</span>
  </div>
</article>"""

def open_slot(label="Category open"):
    return f"""<div class="slot">
  <span class="tag tag-open">Founding slot</span>
  <h3>{e(label)}</h3>
  <p>We are reviewing brands for this category now. Independent stores only.</p>
  <a class="btn btn-sm btn-ghost" href="/join/" style="align-self:flex-start">Apply to list</a>
</div>"""

# ---------------------------------------------------------------- pages
def page_home():
    by_cat = {c["slug"]: len([p for p in PRODUCTS if p.get("category") == c["slug"]]) for c in CATS}
    live   = [c for c in CATS if by_cat[c["slug"]]]
    open_c = [c for c in CATS if not by_cat[c["slug"]]]
    ix_live = "".join(index_entry(c["name"], f'/c/{c["slug"]}/', by_cat[c["slug"]]) for c in live)
    ix_open = "".join(index_entry(c["name"], f'/c/{c["slug"]}/', "\u2014") for c in open_c)
    reg = "".join(register_row(i + 1, s) for i, s in enumerate(STORES))

    # one plate per type, so the opening spread shows the range rather than eight shower doors
    seen, spread = set(), []
    for x in PRODUCTS:
        if x.get("subcategory") in seen: continue
        seen.add(x.get("subcategory")); spread.append(x)
        if len(spread) == 8: break
    spread_html = "".join(plate(x, i+1) for i, x in enumerate(spread))

    # four real listings, one per type, for the hero. No photo, no tile.
    art = [x for x in spread if x.get("image")][:4]
    hero_tiles = "".join(
        f'<a class="htile" href="{e(x["url"])}" rel="nofollow noopener" target="_blank">'
        f'<img src="{e(x["image"])}" alt="{e(x["title"])}" loading="eager" decoding="async">'
        f'<span class="htile-cap"><b>{e(x["subcategory"])}</b>{money_mono(x["price"])}</span></a>'
        for x in art)
    deep = PRODUCTS[8:20]

    types_n, brands_n = len(TYPES), len(BRANDS)
    prices = sorted(float(x["price"]) for x in PRODUCTS if x.get("price"))

    ld = [{"@context":"https://schema.org","@type":"WebSite","name":BRAND,"url":BASE+"/",
           "potentialAction":{"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":BASE+"/search/?q={search_term_string}"},"query-input":"required name=search_term_string"}},
          {"@context":"https://schema.org","@type":"Organization","name":BRAND,"url":BASE+"/","description":SITE["pitch"]}]

    body = f"""{header()}
<main id="main"><div class="wrap">
  <p class="orient">
    <b>{len(STORES)}</b> store{"s" if len(STORES)!=1 else ""}<span class="sep">/</span>
    <b>{len(PRODUCTS)}</b> listing{"s" if len(PRODUCTS)!=1 else ""}<span class="sep">/</span>
    <b>{types_n}</b> types<span class="sep">/</span><b>{brands_n}</b> brands<span class="sep">/</span>
    compiled <b>{TODAY}</b><span class="sep">/</span>commission taken <b>0%</b>
  </p>

  <section class="hero">
    <div class="hero-copy">
      <h1>Buy it from the people who make it.</h1>
      <p>{e(BRAND)} is an index of independent online stores. Search it, find the thing, then buy on the seller's own site. We never handle the money, so nothing here is marked up to pay us and no listing is bought.</p>
      <span class="after">
        <a href="#goods">See the goods</a>
        <a href="/contents/">Browse by type</a>
      </span>
      <p class="hero-trust">{socket_svg(20)} <span>Independent sellers only &middot; every link goes to their own checkout &middot; <b>0% commission</b></span></p>
    </div>

    <aside class="hero-art" aria-label="A sample of what is listed">
      <div class="hero-grid">{hero_tiles}</div>
      <a class="hero-cta" href="/join/">
        {plug_svg(26)}
        <span>
          <b>Sell something good?</b>
          Plug your store in from {money(SITE["price_entry"])} a month &mdash; and keep every cent of the sale.
        </span>
        <span class="go" aria-hidden="true">&rarr;</span>
      </a>
    </aside>
  </section>
</div>

<div class="bleed bleed-tint" id="goods"><div class="wrap">
  <div class="rule" style="margin-top:0"><h2>Plates</h2><span class="n">one from each of the first eight types</span>
    <a class="more" href="/contents/">All {types_n} types \u2192</a></div>
  <div class="plates" style="margin-top:14px">{spread_html}</div>
</div></div>

<div class="wrap">
  <div class="rule" id="index"><h2>Index</h2><span class="n">{len(CATS)} categories</span>
    <a class="more" href="/search/">Search \u2192</a></div>
  <div class="index-list">{ix_live}</div>

  <div class="rule"><h2>Open categories</h2><span class="n">no stores listed yet</span>
    <a class="more" href="/join/">Apply \u2192</a></div>
  <div class="index-list">{ix_open}</div>

  <div class="rule"><h2>Register</h2><span class="n">{len(STORES)} store{"s" if len(STORES)!=1 else ""} on the record</span>
    <a class="more" href="/stores/">All \u2192</a></div>
  <table class="register">
    <thead><tr><th></th><th>Store</th><th>Categories</th><th>Ships to</th><th class="num">Listings</th><th class="num">State</th></tr></thead>
    <tbody>{reg}</tbody>
  </table>
</div>

<div class="bleed bleed-ink" style="margin-top:44px"><div class="wrap">
  <div class="grid g2" style="gap:40px;align-items:center">
    <div>
      <p class="label">For brands</p>
      <p class="claim">If a machine cannot read your store, it <em>cannot recommend it.</em></p>
      <p>The crawlers behind AI assistants do not run JavaScript, do not log in and do not guess. They pass along what is written down in plain text, at a fixed address, with a date on it. Most independent stores publish none of that.</p>
      <p>Building that record is the entire job here, and it costs {money(SITE["price_entry"])} a month with no contract.</p>
      <span class="after" style="display:flex;gap:0 22px;flex-wrap:wrap;margin-top:1rem">
        <a href="/for-brands/" style="border-bottom:1px solid">Why this matters</a>
        <a href="/pricing/" style="border-bottom:1px solid">Pricing</a>
        <a href="/join/" style="border-bottom:1px solid">Apply to list</a>
      </span>
    </div>
    <div class="figures">
      <div class="figure" style="background:#1F2228"><span class="v" style="color:#7FC4B4">0%</span><span class="k" style="color:#9A958B">commission taken</span></div>
      <div class="figure" style="background:#1F2228"><span class="v" style="color:#7FC4B4">{len(PRODUCTS)}</span><span class="k" style="color:#9A958B">listings on the record</span></div>
      <div class="figure" style="background:#1F2228"><span class="v" style="color:#7FC4B4">{types_n}</span><span class="k" style="color:#9A958B">product types indexed</span></div>
      <div class="figure" style="background:#1F2228"><span class="v" style="color:#7FC4B4">{money_mono(prices[0]) if prices else "\u2014"}</span><span class="k" style="color:#9A958B">lowest listed price</span></div>
    </div>
  </div>
</div></div>

<div class="wrap">
  <div class="rule"><h2>Further listings</h2><span class="n">{len(PRODUCTS)} published in all</span>
    <a class="more" href="/search/">Search all \u2192</a></div>
  <div class="rows">{"".join(listing_row(x) for x in deep)}</div>
</div>

<div class="bleed bleed-red" style="margin-top:44px"><div class="wrap">
  <p class="claim" style="margin-bottom:.5rem">Every link here goes to the seller. <em>We never take the transaction.</em></p>
  <p style="max-width:58ch">No commission, no referral fee, no checkout, no affiliate links inside listings. The customer, the email address, the payment and the margin stay with the brand.</p>
  <span class="after" style="display:flex;gap:0 22px;flex-wrap:wrap;margin-top:1rem">
    <a href="/how-it-works/">How it works</a><a href="/about/">About the index</a>
  </span>
</div></div>
</main>
{footer()}"""
    return write("index.html", head(f"{BRAND} \u2014 {SITE['tagline']}",
        "An index of independent online stores. Search real sellers and buy direct from the brand. No marketplace fees, no middleman checkout, no commission.",
        "/", ld=ld, og="default") + body)

def page_category(c):
    trail = [("Home","/"),("Index","/#index"),(c["name"],None)]
    prods  = c["products"]
    stores = c["stores"]
    subs   = sorted({p.get("subcategory") for p in prods if p.get("subcategory")})
    brands = sorted({p.get("brand") for p in prods if p.get("brand")})
    prices = sorted(float(p["price"]) for p in prods if p.get("price"))

    rows = "".join(listing_row(p) for p in prods) if prods else f"""<div class="slot">
  <span class="tag tag-open">Open category</span>
  <h3>No stores listed in {e(c["name"])} yet</h3>
  <p>We are reviewing independent sellers for this category now. Nothing is listed here until a real store connects a real catalog.</p>
  <a class="btn btn-sm btn-brand" href="/join/" style="align-self:flex-start">Apply to list</a>
</div>"""

    nav = "".join(
        f'<a class="ix" href="/c/{o["slug"]}/"{" aria-current=\"page\"" if o["slug"]==c["slug"] else ""}>'
        f'<span class="nm">{e(o["name"])}</span><span class="lead"></span>'
        f'<span class="ct">{len([x for x in PRODUCTS if x.get("category")==o["slug"]]) or "\u2014"}</span></a>'
        for o in CATS)
    subhtml = "".join(f'<label class="chk"><input type="checkbox" data-sub="{e(s)}"> {e(s)}</label>' for s in subs)

    ld = [ld_crumbs(trail),
          {"@context":"https://schema.org","@type":"CollectionPage","name":f"{c['name']} from independent stores",
           "url":f"{BASE}/c/{c['slug']}/","description":c["blurb"],
           "mainEntity":{"@type":"ItemList","numberOfItems":len(prods),
             "itemListElement":[{"@type":"ListItem","position":i+1,"url":p["url"],"name":p["title"]} for i,p in enumerate(prods)]}}]

    band = (f'<span class="sep">/</span> <b>{money_mono(prices[0])}</b> to <b>{money_mono(prices[-1])}</b>' if prices else "")
    body = f"""{header(active=c["slug"])}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(prods)}</b> listing{"s" if len(prods)!=1 else ""}<span class="sep">/</span>
    <b>{len(stores)}</b> store{"s" if len(stores)!=1 else ""}<span class="sep">/</span>
    <b>{len(subs)}</b> type{"s" if len(subs)!=1 else ""}{band}</p>

  <section class="state" style="padding:30px 0 26px">
    <h1>{e(c["name"])}</h1>
    <p>{e(c["blurb"])}</p>
  </section>

  <div class="shell" style="margin-top:22px">
    <div>
      <aside class="side"><h4>Index</h4><div class="index-list" style="columns:1">{nav}</div></aside>
      {'<aside class="side"><h4>Type</h4>' + subhtml + '</aside>' if subhtml else ''}
      {'<aside class="side"><h4>Brands</h4><p class="sm muted" style="margin:0">' + e(", ".join(brands)) + '</p></aside>' if brands else ''}
      <aside class="side"><h4>Machine record</h4>
        <p class="sm muted" style="margin:0 0 8px">This page is published as structured data and an open feed.</p>
        <a class="btn btn-sm btn-ghost" href="/feeds/products.json">Product feed</a></aside>
    </div>
    <div>
      <div class="rule" style="margin-top:0"><h2>Listings</h2><span class="n">{len(prods)} in {e(c["name"])}</span>
        {views_switch() if prods else ""}</div>
      <div id="results">{catalog(prods) if prods else rows}</div>
    </div>
  </div>
</div></main>
{footer()}"""
    return write(f"c/{c['slug']}/index.html",
        head(f"{c['name']} from independent stores | {BRAND}",
             (c["blurb"] + f" {len(prods)} listings from independent sellers, bought direct from the brand.")[:158],
             f"/c/{c['slug']}/", ld=ld, og=f"cat-{c['slug']}",
             og_alt=f"{c['name']} on the {BRAND} index") + body)

def page_store(s):
    trail = [("Home","/"),("Register","/stores/"),(s["name"],None)]
    prods = [p for p in PRODUCTS if p["store"] == s["slug"]]
    cats  = ", ".join(CATBY[c]["name"] for c in s.get("categories", []) if c in CATBY)
    subs  = sorted({p.get("subcategory") for p in prods if p.get("subcategory")})
    brands = sorted({p.get("brand") for p in prods if p.get("brand")})
    prices = sorted(float(p["price"]) for p in prods if p.get("price"))
    withimg = [p for p in prods if p.get("image")]

    # one plate per type for the showcase, so the spread shows the range
    seen, showcase = set(), []
    for x in withimg:
        if x.get("subcategory") in seen: continue
        seen.add(x.get("subcategory")); showcase.append(x)
        if len(showcase) == 8: break

    mosaic = "".join(
        f'<a href="{e(x["url"])}" rel="nofollow noopener" target="_blank" title="{e(x["title"])}">'
        f'<img src="{e(x["image"])}" alt="{e(x["title"])}" loading="lazy" decoding="async"></a>'
        for x in withimg[:5])

    pol = s.get("policy_urls") or {}
    facts = [
        ("Store", f'<a href="{e(s["url"])}" rel="nofollow noopener" target="_blank">{e(host(s["url"]))}</a>'),
        ("Operated by", e(s.get("legal_name") or s["name"])),
        ("Ships from", e(s.get("ships_from") or "Not verified")),
        ("Ships to", e(", ".join(s.get("ships_to", [])) or "Not verified")),
        ("Currency", e(s.get("currency") or "Not verified")),
        ("Categories", " \u00b7 ".join(f'<a href="/c/{c}/">{e(CATBY[c]["name"])}</a>' for c in s.get("categories", []) if c in CATBY)),
        ("Types carried", " \u00b7 ".join(f'<a href="/t/{slug(x)}/">{e(x)}</a>' for x in subs) or "Not verified"),
        ("Brands carried", " \u00b7 ".join(f'<a href="/b/{slug(x)}/">{e(x)}</a>' for x in brands) or "Not verified"),
        ("Price range", f"{money_mono(prices[0])} to {money_mono(prices[-1])}" if prices else "No prices published"),
        ("Returns", e(s.get("returns") or "Not verified") + (f' <a href="{e(pol["returns"])}" rel="nofollow noopener" target="_blank">Policy \u2192</a>' if pol.get("returns") else "")),
        ("Shipping policy", f'<a href="{e(pol["shipping"])}" rel="nofollow noopener" target="_blank">Read the store\u2019s shipping terms \u2192</a>' if pol.get("shipping") else "Not verified"),
        ("Record verified", e(s.get("verified") or "Pending")),
    ]
    spec = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)

    note = "" if s.get("verified") else f"""<div class="note"><p class="sm"><b>Record status:</b> this listing holds only what we can confirm \u2014 the store name and its web address. Unconfirmed fields read <em>not verified</em> rather than being filled in with a guess. If you run this store, <a href="/join/">claim the page</a>.</p></div>"""

    about = e(s["summary"]) if s.get("summary") else (
        f'{e(s["name"])} is an independent online store indexed under {e(cats) or "the index"}. '
        f'Fields we have not confirmed with the store read <em>not verified</em>.')

    empty = f"""<div class="slot">
  <span class="tag">Catalog not connected</span>
  <h3>No product listings published yet</h3>
  <p>{e(s["name"])} has a listing on the index but has not connected a product feed, so we publish no prices or stock for it. Nothing here is estimated.</p>
  <a class="btn btn-sm btn-brand" href="{e(s["url"])}" rel="nofollow noopener" target="_blank" style="align-self:flex-start">Open {e(s["name"])}</a>
</div>"""

    ld = [ld_crumbs(trail),
          {k: v for k, v in {
             "@context":"https://schema.org","@type":"OnlineStore","name":s["name"],"url":s["url"],
             "@id":f"{BASE}/stores/{s['slug']}/#store","sameAs":[s["url"]],
             "legalName": s.get("legal_name") or None,
             "description":s.get("summary") or None,
             "currenciesAccepted":s.get("currency") or None,
             "areaServed":s.get("ships_to") or None,
             "makesOffer":[{"@type":"Offer","name":p["title"],"price":p["price"],"priceCurrency":p.get("currency","USD"),
                            "availability":"https://schema.org/InStock" if p.get("availability")=="in_stock" else "https://schema.org/OutOfStock",
                            "sku":p.get("sku"),"url":p["url"],"image":p.get("image")} for p in prods] or None,
           }.items() if v is not None}]

    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(prods)}</b> listing{"s" if len(prods)!=1 else ""}<span class="sep">/</span>
    <b>{len(subs)}</b> types<span class="sep">/</span><b>{len(brands)}</b> brands<span class="sep">/</span>
    {("<b>verified</b> " + e(s["verified"])) if s.get("verified") else "<b>pending verification</b>"}<span class="sep">/</span>
    commission taken <b>0%</b></p>

  <div class="sheet-top">
    <div>
      <p class="label">Independent store</p>
      <h1 style="font-size:clamp(2.2rem,5vw,3.6rem);margin-bottom:.6rem">{e(s["name"])}</h1>
      <p style="font-size:1.1rem;line-height:1.6;color:var(--ink-2)">{about}</p>
      <span class="after" style="display:flex;gap:0 22px;flex-wrap:wrap;margin-top:1.1rem">
        <a href="{e(s["url"])}" rel="nofollow noopener" target="_blank" style="font:400 1.05rem var(--display);border-bottom:1px solid var(--brand);color:var(--brand-ink)">Visit {e(host(s["url"]))} \u2192</a>
        <a href="/join/" style="font:400 1.05rem var(--display);border-bottom:1px solid var(--line-2);color:var(--ink-2)">Claim this page</a>
      </span>
    </div>
    {f'<div class="mosaic">{mosaic}</div>' if mosaic else ""}
  </div>
  {note}
</div>

<div class="bleed bleed-green"><div class="wrap">
  <div class="figures">
    <div class="figure"><span class="v">{len(prods)}</span><span class="k">listings published</span></div>
    <div class="figure"><span class="v">{len(subs)}</span><span class="k">product types</span></div>
    <div class="figure"><span class="v">{money_mono(prices[0]) if prices else "\u2014"}</span><span class="k">from</span></div>
    <div class="figure"><span class="v">{money_mono(prices[-1]) if prices else "\u2014"}</span><span class="k">to</span></div>
  </div>
</div></div>

<div class="wrap">
  {f'<div class="rule"><h2>Selected plates</h2><span class="n">one from each of {len(showcase)} types</span><a class="more" href="#catalog">Full catalog \u2192</a></div><div class="plates" style="margin-top:14px">{"".join(plate(x, i+1) for i, x in enumerate(showcase))}</div>' if showcase else ""}

  <div class="rule"><h2>Record</h2><span class="n">what we publish, and what we have not confirmed</span>
    <a class="more" href="/feeds/stores.json">Feed \u2192</a></div>
  <dl class="spec">{spec}</dl>

  <div class="rule" id="catalog"><h2>Catalog</h2><span class="n">{len(prods)} listing{"s" if len(prods)!=1 else ""}</span>
    {views_switch() if prods else ""}</div>
  {catalog(prods) if prods else empty}

  <p class="sm muted" style="margin-top:16px">Every link goes straight to {e(s["name"])}. {BRAND} takes no commission, handles no payment and sells no placement. Prices, stock and specifications are read from the store's own public catalog and dated {e(s.get("verified") or TODAY)}; check the store for the live figure before you buy.</p>
</div></main>
{footer()}"""
    return write(f"stores/{s['slug']}/index.html",
        head(f"{s['name']} \u2014 independent store | {BRAND}",
             (s.get("summary") or f"{s['name']} is an independent online store at {host(s['url'])}.")[:158],
             f"/stores/{s['slug']}/", ld=ld, og=f"store-{s['slug']}",
             og_alt=f"{s['name']}, an independent store on the {BRAND} index") + body)

def page_stores():
    trail = [("Home","/"),("Register",None)]
    reg = "".join(register_row(i + 1, s) for i, s in enumerate(STORES))
    ld = [ld_crumbs(trail), {"@context":"https://schema.org","@type":"CollectionPage","name":"Register of independent stores","url":BASE+"/stores/",
          "mainEntity":{"@type":"ItemList","numberOfItems":len(STORES),
            "itemListElement":[{"@type":"ListItem","position":i+1,"url":f"{BASE}/stores/{s['slug']}/","name":s["name"]} for i,s in enumerate(STORES)]}}]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(STORES)}</b> store{"s" if len(STORES)!=1 else ""} on the record<span class="sep">/</span>
    <b>{len(PRODUCTS)}</b> listing{"s" if len(PRODUCTS)!=1 else ""}<span class="sep">/</span>compiled <b>{TODAY}</b></p>
  <section class="state" style="padding:30px 0 26px">
    <h1>The register</h1>
    <p>Every store on the index, with what it sells, where it ships and when we last checked. Independent sellers only: each one keeps its own checkout, its own customers and its own margin.</p>
    <span class="after"><a href="/join/">Apply to list</a><a href="/feeds/stores.json">Store feed</a></span>
  </section>
  <div class="rule"><h2>Stores</h2><span class="n">alphabetical by entry</span></div>
  <table class="register">
    <thead><tr><th></th><th>Store</th><th>Categories</th><th>Ships to</th><th class="num">Listings</th><th class="num">State</th></tr></thead>
    <tbody>{reg}</tbody>
  </table>
  <section class="ledge">
    <h2>Your brand belongs on this list.</h2>
    <p>Hand-checked, month to month, no commission and no checkout between you and your customer.</p>
    <span class="after"><a href="/for-brands/">Why list here</a><a href="/pricing/">Pricing</a><a href="/join/">Apply</a></span>
  </section>
</div></main>
{footer()}"""
    return write("stores/index.html", head(f"Register of independent stores | {BRAND}",
        "Every verified independent store on the index, with categories, shipping and verification date. Buy direct from the brand.", "/stores/", ld=ld) + body)

def page_search():
    trail = [("Home","/"),("Search",None)]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(PRODUCTS)}</b> listing{"s" if len(PRODUCTS)!=1 else ""} searchable<span class="sep">/</span>
    <b>{len(STORES)}</b> store{"s" if len(STORES)!=1 else ""}<span class="sep">/</span>results link straight to the seller</p>
  <section class="state" style="padding:30px 0 22px">
    <h1>Search the index</h1>
    <p>One query across every independent store on the record. Results go to the seller's own site \u2014 there is no checkout here.</p>
    <form class="find" action="/search/" method="get" role="search" style="max-width:640px;margin:18px 0 0">
      <label class="sr" for="q2">Search listings</label>
      <input id="q2" name="q" type="search" placeholder="shower pan, sauna, cold plunge, steam generator" autocomplete="off">
      <button type="submit">Search</button>
    </form>
  </section>
  <div class="rule"><h2>Results</h2><span class="n" id="rcount">Type to search</span>
    <select id="sort2" class="more" aria-label="Sort" style="margin-left:auto">
      <option value="rel">Order: relevance</option>
      <option value="lo">Price: low to high</option>
      <option value="hi">Price: high to low</option></select></div>
  <div class="rows" id="results"></div>
  <p class="muted sm" style="margin-top:14px" id="empty">Nothing matched. Try a broader word, or <a href="/stores/">browse the register</a>.</p>
</div></main>
{footer()}"""
    return write("search/index.html", head(f"Search independent stores | {BRAND}",
        "Search listings across every independent store on the index.", "/search/",
        extra='<meta name="robots" content="noindex, follow">', ld=ld_crumbs(trail)) + body)

def page_for_brands():
    trail = [("Home","/"),("For brands",None)]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap mid">
  <p class="eyebrow">For brands</p>
  <h1>Your store is a web app. The things recommending products can't run it.</h1>
  <p class="lede">A shopper asks an assistant for a frameless shower door under a thousand dollars. The assistant answers from what it can retrieve and parse. If your catalog is drawn by JavaScript, your prices live inside images, or your spec sheet is a PDF behind a filter, you are not in the running &mdash; not because you lost, but because you were never legible.</p>

  <div class="note"><p>This is not a marketing problem. It is a file-format problem that looks like a marketing problem.</p></div>

  <h2 class="mt2">The three things that decide whether you can be recommended</h2>
  <div class="steps mt2">
    <div class="step"><div><h3>1. Can it be fetched?</h3>
      <p>The crawlers behind the major assistants request your page and read what comes back in that first response. They do not wait for your framework to boot, they do not click, they do not log in, and they do not run the script that fills your product grid. Open your own store in a browser with JavaScript switched off. Whatever is still on the screen is roughly what a machine sees. For a lot of modern storefronts, that is a logo and a spinner.</p></div></div>
    <div class="step"><div><h3>2. Can it be parsed?</h3>
      <p>A price is only a price if it is characters in the HTML. Rendered into an image, injected by a script, or shown only after a variant is selected, it is invisible &mdash; and a machine that cannot state your price will quote someone who publishes theirs plainly. Same for what you ship, where you ship it, how long returns take and what the thing actually is.</p></div></div>
    <div class="step"><div><h3>3. Can it be trusted as current?</h3>
      <p>The ugliest failure in machine-generated recommendations is not a made-up store. It is a real store with a dead price, a sold-out item, or an address it moved out of two years ago. Undated records get treated as risky, and risky records get skipped. A visible, honest verification date is cheap to publish and does more work than almost anything else on the page.</p></div></div>
  </div>

  <h2 class="mt2">What we actually build for you</h2>
  <div class="split mt2">
    <div>
      <h3>A page designed for the reader you can't see</h3>
      <ul>
        <li>Server-rendered HTML. Complete in the first response, no JavaScript required to read a single word of it.</li>
        <li>Your prices, materials, sizes, shipping and returns written out in prose, where a model will actually read them &mdash; and marked up in schema.org as well, because the markup is what makes you eligible for product feeds.</li>
        <li>A verification date on the record, re-checked on a schedule, so nothing we publish about you goes quietly stale.</li>
        <li>Real sentences about what you make. Not keyword soup. The thing being retrieved is language, so the language has to be worth retrieving.</li>
      </ul>
    </div>
    <div>
      <h3>A feed, because pages alone are not the whole surface</h3>
      <ul>
        <li>Your catalog published as open JSON and as a tab-separated feed in the column shape the agentic-commerce product feed specs use.</li>
        <li>A stable URL that does not move, so anything that ingested it once can refresh it.</li>
        <li>Submission into the merchant feed programs that put products into AI shopping results &mdash; the paperwork most independent stores never get around to.</li>
        <li>The index exposed as an MCP server, so an assistant can <em>query</em> us for your products instead of hoping it crawled you recently enough.</li>
      </ul>
    </div>
  </div>

  <h2 class="mt2">Why a third-party page helps when you already have a website</h2>
  <p>Two reasons, and neither is magic.</p>
  <p><b>Retrieval likes corroboration.</b> One page saying you are good is a claim. A page you control plus an independent index that lists you, dates you and describes you in different words is a corroborated claim, and corroborated claims survive summarisation better. You are not replacing your store. You are giving the machine a second, cleaner source that agrees with it.</p>
  <p><b>Category pages outrank store pages for category questions.</b> "Who sells frameless shower doors" is a question about a set. Sets live on index pages. You want to be on the page that answers the question, and that page is almost never your homepage.</p>

  <h2 class="mt2">What this costs you versus what a marketplace costs you</h2>
  <p>On a large marketplace you pay a referral fee for the sale. Then you pay again, in advertising, to be found among the other listings &mdash; including listings for your own product. If you use their fulfilment you pay a third time. Three separate takes out of one sale, and at the end of it the buyer is their customer, not yours: their email, their reorder, their reviews, their data about what sells.</p>
  <p>We take none of it. No commission, no referral fee, no checkout, no affiliate links inside listings. Every link on this site goes to your own store. The customer, the email address, the payment and the margin stay with you. The only thing we sell is being legible.</p>

  <div class="split pair mt2">
    <div>
      <h3>Who this is for</h3>
      <ul>
        <li>You sell your own products, or you are a real specialist retailer, not a dropship front.</li>
        <li>You control your own checkout.</li>
        <li>Your margin is good enough that being found is worth more to you than being cheapest.</li>
        <li>You would rather own a customer than rent one.</li>
      </ul>
    </div>
    <div>
      <h3>Who this is not for</h3>
      <ul>
        <li>You want a guaranteed number of clicks. Nobody can honestly promise that, and we will not pretend to.</li>
        <li>You want us to run your checkout. We never will &mdash; that is the point of the model.</li>
        <li>You are reselling the same catalog as four hundred other stores at the same price. Being legible will not fix that.</li>
      </ul>
    </div>
  </div>

  <div class="note"><p><b>What we will not claim:</b> we cannot promise you a citation in any assistant, a search ranking, or a sale. What we can promise is that every fact about you is published in a form a machine can fetch, parse and date &mdash; and that is the part that is currently missing. Anyone selling you the guarantee is selling you something they do not control.</p></div>

  <div class="band mt2">
    <h2>{money(SITE["price_entry"])} a month. Cancel whenever.</h2>
    <p>No minimum term, no buyout clause, no auto-renewing multi-year paper, no early termination fee. If it stops being worth it, you stop paying, and you take your page with you.</p>
    <div class="hero-cta"><a class="btn btn-lg" href="/pricing/">See pricing</a>
      <a class="btn btn-lg btn-ghost" style="color:#fff;border-color:#41414E" href="/join/">Apply to list</a></div>
  </div>
</div></main>
{footer()}"""
    return write("for-brands/index.html", head(f"Why list your brand on {BRAND}",
        "AI assistants recommend what they can fetch, parse and date. Most independent storefronts fail all three. We publish the machine-readable record that fixes it. From $19.99/mo, no contract.",
        "/for-brands/", ld=ld_crumbs(trail)) + body)

def page_pricing():
    trail = [("Home","/"),("Pricing",None)]
    tiers = [
        ("Index", SITE["price_entry"], "per month", False, [
            ("Your own brand page on the index", 1), ("Listed in every category you sell in", 1),
            ("Server-rendered, structured data, prices in prose", 1), ("Included in the public store and product feeds", 1),
            ("Verification date, re-checked quarterly", 1), ("Up to 10 product listings", 1),
            ("Merchant feed syndication", 0), ("Custom skin and colours", 0)]),
        ("Pro", 49, "per month", True, [
            ("Everything in Index", 1), ("Up to 250 product listings", 1),
            ("Feed syndication to the major merchant feed programs", 1), ("Your record exposed through our MCP server", 1),
            ("Priority placement in your categories", 1), ("Monthly visibility report: who cites you, and for what", 1),
            ("Colour, logo and skin controls", 1), ("Catalog auto-sync", 0)]),
        ("Signal", 149, "per month", False, [
            ("Everything in Pro", 1), ("Unlimited listings with nightly catalog sync", 1),
            ("Merchant feed applications applied for on your behalf", 1), ("Answer monitoring across the major assistants", 1),
            ("Custom skin, or bring your own HTML", 1), ("Quarterly machine-readability audit of your own store", 1),
            ("Named contact, same-day support", 1), ("Fully managed, nothing for you to do", 1)]),
    ]
    cards = ""
    for name, amt, per, pick, feats in tiers:
        li = "".join(f'<li class="{"" if ok else "no"}">{e(t)}</li>' for t, ok in feats)
        a = f'<sup>$</sup>{int(amt)}' if float(amt).is_integer() else f'<sup>$</sup>{amt}'
        cards += f"""<div class="tier{" pick" if pick else ""}">
  {'<span class="tag tag-brand" style="align-self:flex-start;margin-bottom:10px">Most brands pick this</span>' if pick else ''}
  <div class="nm">{e(name)}</div>
  <div class="amt">{a}</div>
  <div class="per">{e(per)} · cancel anytime</div>
  <ul>{li}</ul>
  <a class="btn {"btn-brand" if pick else ""}" href="/join/?plan={e(name.lower())}">Start on {e(name)}</a>
</div>"""

    addons = [("Brand page build, written for you", "$249 once"),
              ("Catalog import and clean-up, up to 500 items", "$399 once"),
              ("Custom skin designed to your brand", "$499 once"),
              ("Machine-readability fix pack for your own store", "$750 once"),
              ("Full store build, hosted by you, yours outright", "from $3,000 once")]
    addhtml = "".join(f'<div class="card"><div class="flex between"><h3 style="margin:0;font-size:.98rem">{e(n)}</h3><span class="rail"><b>{e(p)}</b></span></div></div>' for n, p in addons)

    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <div class="sec-head"><div><p class="eyebrow">Pricing</p><h1>Priced like software, not like a phone contract.</h1>
    <p class="lede" style="margin:0">Month to month. No minimum term, no auto-renewing multi-year paper, no early termination fee, no buyout clause. Cancel in the dashboard. There is no free tier, because a free listing nobody maintains is the thing that does not work.</p></div></div>
  <div class="tiers mt2">{cards}</div>

  <div class="sec"><h2>One-time add-ons</h2>
    <p class="muted sm">Optional. Nothing here is required to stay listed.</p>
    <div class="grid" style="gap:8px;margin-top:14px">{addhtml}</div>
  </div>

  <div class="split">
    <div><h3>What we will never do</h3>
      <ul><li>Lock you into a multi-year term</li><li>Charge an early termination or buyout fee</li><li>Take a commission on your sales</li><li>Sit between you and your customer at checkout</li><li>Bill you for anything you did not order</li></ul></div>
    <div><h3>What you can always do</h3>
      <ul><li>Export your page as plain HTML and take it</li><li>Download your own feed, any time</li><li>Cancel in one click and keep your domain, data and customers</li><li>Move up or down a tier at any time, prorated</li></ul></div>
  </div>
</div></main>
{footer()}"""
    return write("pricing/index.html", head(f"Pricing | {BRAND}",
        f"From {money(SITE['price_entry'])} a month, cancel anytime. No contracts, no commission, no checkout fees.",
        "/pricing/", ld=ld_crumbs(trail)) + body)

def page_how():
    trail = [("Home","/"),("How it works",None)]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap mid">
  <p class="eyebrow">How it works</p>
  <h1>Two audiences. One record.</h1>
  <p class="lede">Shoppers use the index like any store directory. Assistants use the same pages as a source. Both read the identical record, which is the point.</p>

  <h2 class="mt2">If you are shopping</h2>
  <div class="steps">
    <div class="step"><div><h3>Search or browse a category</h3><p>Every listing is an independent store, not a reseller and not a marketplace account.</p></div></div>
    <div class="step"><div><h3>Click through to the brand</h3><p>You land on the seller's own site. We take no commission, so nothing is marked up to pay us.</p></div></div>
    <div class="step"><div><h3>Buy from them, not from us</h3><p>Their checkout, their returns policy, their customer service. Your relationship is with the brand.</p></div></div>
  </div>

  <h2 class="mt2">If you are a brand</h2>
  <div class="steps">
    <div class="step"><div><h3>Apply and get verified</h3><p>We check that you are a real independent store, note what you sell and where you ship, and date the record.</p></div></div>
    <div class="step"><div><h3>We publish your machine-readable page</h3><p>Server-rendered HTML, structured data, prices written in readable text, a verification date, and a stable feed URL.</p></div></div>
    <div class="step"><div><h3>We push your catalog into the feed programs</h3><p>Merchant feeds are what put products into AI shopping answers. Most independent stores never set one up.</p></div></div>
    <div class="step"><div><h3>We stay callable</h3><p>The index runs as an MCP server, so an assistant can query it live rather than relying on an old crawl.</p></div></div>
    <div class="step"><div><h3>We keep it fresh</h3><p>A dead price or a discontinued product is the most common way these recommendations go wrong, so re-verification is scheduled rather than occasional, and the date is published.</p></div></div>
  </div>

  <h2 class="mt2">What we publish openly</h2>
  <p>All of it is public, documented and free to read. If you can read it, so can an agent.</p>
  <div class="grid g2 mt2">
    <div class="card"><h3>Store feed</h3><p class="sm muted">Every verified store with category, shipping and verification date.</p><a class="btn btn-sm btn-ghost" href="/feeds/stores.json">/feeds/stores.json</a></div>
    <div class="card"><h3>Product feed</h3><p class="sm muted">Every listing with price, currency, availability and a direct URL.</p><a class="btn btn-sm btn-ghost" href="/feeds/products.json">/feeds/products.json</a></div>
    <div class="card"><h3>MCP server</h3><p class="sm muted">Tool definitions so an assistant can query the index directly.</p><a class="btn btn-sm btn-ghost" href="/.well-known/mcp/server.json">/.well-known/mcp/server.json</a></div>
    <div class="card"><h3>Crawler policy</h3><p class="sm muted">Every major AI crawler is allowed. We want to be in the corpus.</p><a class="btn btn-sm btn-ghost" href="/robots.txt">/robots.txt</a></div>
  </div>
</div></main>
{footer()}"""
    return write("how-it-works/index.html", head(f"How {BRAND} works",
        "How the index works for shoppers and for brands, and what we publish openly for machines.",
        "/how-it-works/", ld=ld_crumbs(trail)) + body)

def page_join():
    trail = [("Home","/"),("Plug in",None)]
    opts = "".join(f'<option value="{c["slug"]}">{e(c["name"])}</option>' for c in CATS)
    F = SITE.get("form") or {}
    endpoint = F.get("endpoint")

    fields = f"""      <div class="field"><label for="f-store">Store name</label>
        <input id="f-store" name="Store name" autocomplete="organization" required></div>
      <div class="field"><label for="f-url">Store URL</label>
        <input id="f-url" name="Store URL" type="url" inputmode="url" placeholder="https://" autocomplete="url" required></div>
      <div class="field"><label for="f-email">Your email</label>
        <input id="f-email" name="email" type="email" inputmode="email" autocomplete="email" required></div>
      <div class="field"><label for="f-cat">Main category</label>
        <select id="f-cat" name="Category">{opts}</select></div>
      <div class="field"><label for="f-plan">Plan</label><select id="f-plan" name="Plan">
        <option value="Index {money(SITE["price_entry"])}/mo">Index &mdash; {money(SITE["price_entry"])}/mo</option>
        <option value="Pro $49/mo">Pro &mdash; $49/mo</option>
        <option value="Signal $149/mo">Signal &mdash; $149/mo</option>
        <option value="Not sure yet">Not sure yet &mdash; tell me which fits</option></select></div>
      <div class="field"><label for="f-note">What do you make or sell?</label>
        <textarea id="f-note" name="What they sell" rows="4" placeholder="A couple of sentences is plenty. If you have a catalog feed or a sitemap, mention it."></textarea></div>
      <div class="field"><label for="f-how">Anything else?</label>
        <input id="f-how" name="Notes" placeholder="Optional &mdash; how you found us, questions, timing"></div>"""

    if endpoint:
        # FormSubmit: _honey is the honeypot (bots fill it, people never see it),
        # _captcha off because the honeypot already does that job without making
        # a real applicant solve a puzzle, _next is our own thank-you page.
        hp = e(F.get("honeypot") or "_honey")
        form = f"""<form class="apply" method="POST" action="{e(endpoint)}" id="apply">
      <input type="hidden" name="_subject" value="{e(F.get("subject") or (BRAND + " — new store application"))}">
      <input type="hidden" name="_template" value="{e(F.get("template") or "table")}">
      <input type="hidden" name="_captcha" value="{"true" if F.get("captcha") else "false"}">
      <input type="hidden" name="_next" value="{BASE}/join/thanks/">
      <div class="hp" aria-hidden="true">
        <label for="f-hp">Leave this field empty</label>
        <input id="f-hp" type="text" name="{hp}" tabindex="-1" autocomplete="off">
      </div>
{fields}
      <button class="btn btn-brand btn-lg" type="submit" style="width:100%">Send application</button>
      <p class="xs muted" style="margin:.85rem 0 0">No card needed. Nothing is charged until your page is live and you have approved it.</p>
    </form>"""
    else:
        form = f"""<div class="apply">
      <span class="tag tag-brand">Opening to founding stores</span>
      <h3 style="margin:.7rem 0 .5rem">The form is not wired up yet</h3>
      <p class="sm">Contact {e(SITE["publisher"])} through <a href="{e(SITE["publisher_url"])}">{e(host(SITE["publisher_url"]))}</a> with your store URL.</p>
    </div>"""

    ld = [ld_crumbs(trail),
          {"@context":"https://schema.org","@type":"WebPage","name":f"Plug your store into {BRAND}",
           "url":BASE+"/join/","description":"Apply to list your independent store. Hand-checked, month to month, no commission."},
          {"@context":"https://schema.org","@type":"Service","name":f"{BRAND} store listing",
           "provider":{"@id":BASE+"/#org"},
           "serviceType":"Online store directory listing and machine-readable product record",
           "areaServed":"Worldwide",
           "offers":{"@type":"Offer","price":str(SITE["price_entry"]),"priceCurrency":"USD",
                     "url":BASE+"/pricing/","availability":"https://schema.org/InStock"}}]

    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(STORES)}</b> store{"s" if len(STORES)!=1 else ""} listed<span class="sep">/</span>
    hand-checked<span class="sep">/</span>month to month<span class="sep">/</span>
    commission taken <b>0%</b></p>

  <section class="state" style="padding:40px 0 30px">
    <p class="label">Plug in</p>
    <h1>Plug your store in. <em>Keep every cent of the sale.</em></h1>
    <p>You already have a store, a checkout and customers. We do not want any of them. What you get here is a page built so machines can read you, in an index shoppers search &mdash; and every link on it goes straight to your own site.</p>
  </section>
</div>

<div class="bleed bleed-green"><div class="wrap">
  <div class="figures">
    <div class="figure"><span class="v">0%</span><span class="k">commission on your sales</span></div>
    <div class="figure"><span class="v">{money(SITE["price_entry"])}</span><span class="k">a month to start</span></div>
    <div class="figure"><span class="v">0</span><span class="k">months minimum term</span></div>
    <div class="figure"><span class="v">2</span><span class="k">business days to a decision</span></div>
  </div>
</div></div>

<div class="wrap">
  <div class="shell" style="margin-top:34px;grid-template-columns:1.05fr .95fr;gap:44px">
    <div>
      <div class="rule" style="margin-top:0"><h2>Apply</h2><span class="n">takes about two minutes</span></div>
      <div style="margin-top:18px">{form}</div>
    </div>

    <div>
      <div class="rule" style="margin-top:0"><h2>What happens next</h2></div>
      <div class="steps" style="margin-top:16px">
        <div class="step"><div><h3>1. We check you are real</h3>
          <p class="sm">That you are an independent seller rather than a marketplace reseller front, that you run your own checkout, that the products and prices on your site are current, and that you ship somewhere reliably. Usually two business days.</p></div></div>
        <div class="step"><div><h3>2. We build your record</h3>
          <p class="sm">Server-rendered page, your facts written as text and marked up in schema.org, your catalog read from your own feed, a verification date, and your listing in every category, type and brand index it belongs in.</p></div></div>
        <div class="step"><div><h3>3. You approve it</h3>
          <p class="sm">You see the page before anyone else does. Nothing about your store gets published that you have not read. Anything wrong, we fix and re-date it.</p></div></div>
        <div class="step"><div><h3>4. Billing starts the day you are live</h3>
          <p class="sm">Not at application, not at approval. From then it is month to month, cancel in one click, and you keep your page export and your data on the way out.</p></div></div>
      </div>

      <div class="rule"><h2>What we never do</h2></div>
      <div class="split pair" style="margin-top:16px">
        <div>
          <h3>Yours, always</h3>
          <ul>
            <li>The customer, their email, and the reorder</li>
            <li>The payment and the full margin</li>
            <li>Your checkout, your returns, your service</li>
            <li>Your data, exportable any time</li>
          </ul>
        </div>
        <div>
          <h3>Never ours to sell</h3>
          <ul>
            <li>A cut of your sales &mdash; there is none</li>
            <li>Your position in the index</li>
            <li>An unlabelled placement</li>
            <li>Your details, to anyone</li>
          </ul>
        </div>
      </div>

      <div class="note"><p class="sm"><b>We will never ask you</b> for your store password, your payment processor login, or your domain registrar credentials. We do not need them, and anyone claiming to be us who asks is not us.</p></div>
    </div>
  </div>

  <div class="ledge">
    <h2>Not sure it is worth {money(SITE["price_entry"])} a month?</h2>
    <p>Open your own store in a browser with JavaScript switched off. Whatever is still on screen is roughly what a machine sees when it fetches your page. If that is a logo and a spinner, you already know why this exists.</p>
    <span class="after"><a href="/for-brands/">Read the argument</a><a href="/pricing/">Compare the tiers</a><a href="/faq/">Questions</a></span>
  </div>
</div></main>
{footer()}"""
    return write("join/index.html", head(f"Plug your store into {BRAND}",
        f"Apply to list your independent store. Hand-checked, month to month, no commission, no checkout between you and your customer. From {money(SITE['price_entry'])}.",
        "/join/", ld=ld) + body)

def page_thanks():
    trail = [("Home","/"),("Plug in","/join/"),("Received",None)]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap narrow">
  <section class="state" style="padding:46px 0 32px">
    <p class="label">Application received</p>
    <h1>Got it. <em>Now we go and check.</em></h1>
    <p>Your application is in. A person reads every one of these, which is why it takes a couple of days rather than a couple of seconds.</p>
  </section>

  <div class="rule" style="margin-top:0"><h2>What happens from here</h2></div>
  <div class="steps" style="margin-top:16px">
    <div class="step"><div><h3>Within two business days</h3>
      <p>We check that you are an independent seller, that you run your own checkout, and that your products and prices are current. If something does not add up we ask you rather than guess.</p></div></div>
    <div class="step"><div><h3>Then we build your record</h3>
      <p>Your page, your catalog read from your own feed, and your listing in every category, type and brand index it belongs in.</p></div></div>
    <div class="step"><div><h3>You approve it before anyone sees it</h3>
      <p>Nothing about your store is published until you have read it. Billing starts the day you go live, not before.</p></div></div>
  </div>

  <div class="note"><p class="sm"><b>Nothing arrived?</b> Check your spam folder for our reply, and add our address to your contacts. If you hear nothing in three business days, <a href="/contact/">chase us</a> &mdash; something went wrong and we would rather know.</p></div>

  <div class="ledge">
    <h2>While you wait</h2>
    <p>Open your own store with JavaScript switched off. Whatever is still on screen is what a machine sees. It is the clearest two minutes you can spend on this.</p>
    <span class="after"><a href="/for-brands/">Why that matters</a><a href="/">Browse the index</a><a href="/faq/">Questions</a></span>
  </div>
</div></main>
{footer()}"""
    return write("join/thanks/index.html", head(f"Application received | {BRAND}",
        "Your application is in. A person reviews every one, usually within two business days.",
        "/join/thanks/", extra='<meta name="robots" content="noindex, follow">',
        ld=ld_crumbs(trail)) + body)

def page_about():
    trail = [("Home","/"),("About",None)]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap narrow">
  <p class="eyebrow">About</p>
  <h1>We are the record, not the middleman.</h1>
  <p class="lede">{e(BRAND)} is an index of independent online stores. We do not host checkout, hold inventory, take a commission or stand between a brand and its customer.</p>
  <h2>Why we exist</h2>
  <p>Discovery moved. People used to find products by searching and clicking. Increasingly they ask an assistant, and the assistant answers from whatever record it can retrieve. Large retailers are already inside those systems. Independent stores, overwhelmingly, are not.</p>
  <p>The gap is not quality. It is legibility. The systems doing the recommending can only pass along what they can fetch, parse and date &mdash; plain text at a stable address, with prices written out and a timestamp on the record. A great store whose catalog is drawn by JavaScript and whose prices live inside images is, to those systems, a blank page. That is a fixable problem, and fixing it is all we do.</p>
  <h2>How we make money</h2>
  <p>Brands pay a monthly fee to be on the index and kept current. That is the whole model. We take no cut of any sale, we run no affiliate links in listings, and we do not sell placement that is disguised as editorial. Anything sponsored is labelled.</p>
  <h2>How we handle accuracy</h2>
  <p>Every store record carries a verification date, and a record we have not verified says so plainly instead of filling the gaps with a plausible guess. If a field reads <em>not verified</em>, that is not an oversight; it means we have not confirmed it and will not invent it. If something here is wrong, tell us and we will correct it and re-date the record.</p>
  <h2>What we will not publish</h2>
  <p>No invented products, no estimated prices, no stock levels we have not checked, no reviews we did not receive, and no affiliate links inside listings. If this index ever looks smaller than a competitor, that is the reason.</p>
  <h2>Who runs it</h2>
  <p>{e(BRAND)} is published by <a href="{SITE["publisher_url"]}">{e(SITE["publisher"])}</a>.</p>
</div></main>
{footer()}"""
    return write("about/index.html", head(f"About {BRAND}",
        "An index of independent online stores. No commission, no checkout, no middleman.",
        "/about/", ld=ld_crumbs(trail)) + body)

def page_404():
    body = f"""{header()}
<main id="main"><div class="wrap narrow sec">
  <p class="eyebrow">404</p><h1>That page is not on the index.</h1>
  <p class="lede">It may have moved, or the store may have left.</p>
  <div class="hero-cta mt2"><a class="btn btn-brand" href="/">Back to the index</a><a class="btn btn-ghost" href="/stores/">All stores</a></div>
</div></main>
{footer()}"""
    return write("404.html", head(f"Not found | {BRAND}", "Page not found.", "/404.html",
        extra='<meta name="robots" content="noindex, follow">') + body)

def page_facet(kind, key, rec):
    """One page per product type (/t/) or brand (/b/). Same shape, different axis."""
    items = rec["items"]
    name  = rec["name"]
    label = "Type" if kind == "t" else "Brand"
    base  = "/t/" if kind == "t" else "/b/"
    others = TYPES if kind == "t" else BRANDS
    trail = [("Home","/"),("Index","/#index"),(name,None)]

    prices = sorted(float(i["price"]) for i in items if i.get("price"))
    stores = sorted({STOREBY.get(i["store"],{}).get("name", i["store"]) for i in items})
    cross  = sorted({(i.get("brand") if kind=="t" else i.get("subcategory")) for i in items if (i.get("brand") if kind=="t" else i.get("subcategory"))})
    cats   = sorted({CATBY[i["category"]]["name"] for i in items if i.get("category") in CATBY})

    CUR = ' aria-current="page"'
    nav = "".join(
        f'<a class="ix" href="{base}{k}/"{CUR if k == key else ""}>'
        f'<span class="nm">{e(v["name"])}</span><span class="lead"></span>'
        f'<span class="ct">{len(v["items"])}</span></a>' for k, v in others.items())

    if kind == "t":
        lede = (f"Every {name.lower()} on the index, from every independent store listed. "
                f"Prices and specifications are read from each seller's own catalog and dated. "
                f"Buying happens on their site, not here.")
        crosslabel, crossbase = "Brands in this type", "/b/"
    else:
        lede = (f"Everything by {name} carried by independent stores on the index. "
                f"We are not {name} and we do not sell it \u2014 we record who does, "
                f"so you can buy from a real seller rather than guess.")
        crosslabel, crossbase = "Types carried", "/t/"
    crosshtml = " \u00b7 ".join(f'<a href="{crossbase}{slug(x)}/">{e(x)}</a>' for x in cross)

    ld = [ld_crumbs(trail),
          {"@context":"https://schema.org","@type":"CollectionPage","name":f"{name} \u2014 {BRAND}",
           "url":f"{BASE}{base}{key}/","description":lede,
           "mainEntity":{"@type":"ItemList","numberOfItems":len(items),
             "itemListElement":[{"@type":"ListItem","position":i+1,"url":x["url"],"name":x["title"]}
                                for i,x in enumerate(items)]}}]

    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(items)}</b> listing{"s" if len(items)!=1 else ""}<span class="sep">/</span>
    <b>{len(stores)}</b> store{"s" if len(stores)!=1 else ""}
    {f'<span class="sep">/</span> <b>{money_mono(prices[0])}</b> to <b>{money_mono(prices[-1])}</b>' if prices else ""}
    <span class="sep">/</span>compiled <b>{TODAY}</b></p>

  <section class="state" style="padding:32px 0 26px">
    <p class="label">{label}</p>
    <h1>{e(name)}</h1>
    <p>{lede}</p>
  </section>

  <div class="shell" style="margin-top:22px">
    <div>
      <aside class="side"><h4>All {("types" if kind=="t" else "brands")}</h4>
        <div class="index-list" style="columns:1">{nav}</div></aside>
      <aside class="side"><h4>{crosslabel}</h4><p class="sm" style="margin:0">{crosshtml}</p></aside>
      <aside class="side"><h4>Categories</h4><p class="sm" style="margin:0">{e(", ".join(cats))}</p></aside>
      <aside class="side"><h4>Sold by</h4><p class="sm" style="margin:0">{e(", ".join(stores))}</p></aside>
    </div>
    <div>
      <div class="rule" style="margin-top:0"><h2>Listings</h2><span class="n">{len(items)} under {e(name)}</span>
        {views_switch()}</div>
      <div id="results">{catalog(items)}</div>
    </div>
  </div>
</div></main>
{footer()}"""
    return write(f"{base.strip('/')}/{key}/index.html",
        head(f"{name} from independent stores | {BRAND}", lede[:158], f"{base}{key}/", ld=ld,
             og=f"{'type' if kind=='t' else 'brand'}-{key}", og_alt=f"{name} on the {BRAND} index") + body)

def page_indexes():
    """A contents page listing every way into the index."""
    trail = [("Home","/"),("Contents",None)]
    def block(title, base, coll):
        return (f'<div class="rule"><h2>{title}</h2><span class="n">{len(coll)} entries</span></div>'
                '<div class="index-list">' +
                "".join(index_entry(v["name"], f'{base}{k}/', len(v["items"])) for k, v in coll.items()) +
                "</div>")
    cat_block = ('<div class="rule" style="margin-top:0"><h2>Categories</h2>'
                 f'<span class="n">{len(CATS)} entries</span></div><div class="index-list">' +
                 "".join(index_entry(c["name"], f'/c/{c["slug"]}/',
                                     len([p for p in PRODUCTS if p.get("category")==c["slug"]]) or "\u2014")
                         for c in CATS) + "</div>")
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(CATS)}</b> categories<span class="sep">/</span>
    <b>{len(TYPES)}</b> types<span class="sep">/</span><b>{len(BRANDS)}</b> brands<span class="sep">/</span>
    <b>{len(STORES)}</b> store{"s" if len(STORES)!=1 else ""}<span class="sep">/</span>compiled <b>{TODAY}</b></p>
  <section class="state" style="padding:32px 0 26px">
    <p class="label">Contents</p>
    <h1>Every way into the index.</h1>
    <p>Browse by editorial category, by product type as the sellers themselves classify it, or by the brand that made the thing. Counts are literal: a dash means nothing is listed under that heading yet.</p>
  </section>
  {cat_block}
  {block("Product types", "/t/", TYPES)}
  {block("Brands carried", "/b/", BRANDS)}
</div></main>
{footer()}"""
    return write("contents/index.html", head(f"Contents \u2014 every category, type and brand | {BRAND}",
        f"The full contents of the index: {len(CATS)} categories, {len(TYPES)} product types and {len(BRANDS)} brands carried by independent stores.",
        "/contents/", ld=ld_crumbs(trail)) + body)

def page_contact():
    trail = [("Home","/"),("Contact",None)]
    email = SITE.get("contact_email")
    reach = (f'<a href="mailto:{e(email)}">{e(email)}</a>' if email
             else f'through <a href="{e(SITE["publisher_url"])}">{e(host(SITE["publisher_url"]))}</a>, the publisher')
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient"><b>{len(STORES)}</b> store{"s" if len(STORES)!=1 else ""} on the record<span class="sep">/</span>
    corrections are re-dated, not quietly edited</p>
  <section class="state" style="padding:34px 0 28px">
    <p class="label">Contact</p>
    <h1>Reach a person.</h1>
    <p>There is no ticket queue here and no chatbot. Mail reaches {e(SITE["publisher"])}, which publishes this index.</p>
  </section>

  <div class="rule"><h2>What you probably want</h2><span class="n">pick the nearest one</span></div>
  <div class="grid g2" style="gap:26px;margin-top:18px">
    <div class="card">
      <h3>List your store</h3>
      <p class="sm">Independent sellers only, hand-checked, month to month. Start with the application rather than mail \u2014 it asks for what we need.</p>
      <a class="btn btn-sm btn-brand" href="/join/">Apply to list</a>
    </div>
    <div class="card">
      <h3>Correct something about your store</h3>
      <p class="sm">A wrong price, a stale description, a field marked verified that is not. Tell us what is wrong and we will fix it and re-date the record. You do not need to be a customer to report an error.</p>
      <a class="btn btn-sm btn-ghost" href="/join/">Claim your page</a>
    </div>
    <div class="card">
      <h3>Advertise</h3>
      <p class="sm">We sell listings and labelled sponsorship. We do not sell ranking, and we do not sell placement disguised as editorial.</p>
      <a class="btn btn-sm btn-ghost" href="/advertise/">What we sell</a>
    </div>
    <div class="card">
      <h3>Use our data</h3>
      <p class="sm">The store and product feeds are public and documented, licensed CC-BY-4.0. You do not need permission, only attribution.</p>
      <a class="btn btn-sm btn-ghost" href="/feeds/README.md">Feed documentation</a>
    </div>
  </div>

  <div class="rule"><h2>The details</h2></div>
  <dl class="spec">
    <div><dt>Published by</dt><dd><a href="{e(SITE["publisher_url"])}">{e(SITE["publisher"])}</a></dd></div>
    <div><dt>Reach us</dt><dd>{reach}</dd></div>
    <div><dt>Response time</dt><dd>Two business days for applications. Corrections are treated as urgent.</dd></div>
    <div><dt>Press and data questions</dt><dd>Same address. The figures on this site are all derived from the public feeds, so most questions can be answered from <a href="/feeds/README.md">the feed documentation</a> faster than we can answer them.</dd></div>
  </dl>

  <div class="note"><p class="sm"><b>We will never ask you</b> for your store password, your payment processor login or your domain registrar credentials. If anyone claiming to be us does, it is not us.</p></div>
</div></main>
{footer()}"""
    return write("contact/index.html", head(f"Contact | {BRAND}",
        f"Reach {BRAND}: list a store, correct a record, ask about advertising, or use the open data feeds.",
        "/contact/", ld=ld_crumbs(trail)) + body)

def page_advertise():
    trail = [("Home","/"),("Advertise",None)]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <p class="orient">labelled placements only<span class="sep">/</span>
    ranking is <b>not</b> for sale<span class="sep">/</span>no affiliate links in listings</p>
  <section class="state" style="padding:34px 0 28px">
    <p class="label">Advertise</p>
    <h1>We sell attention, not credibility.</h1>
    <p>Everything on this page is bought in the open and labelled where it appears. The order of the index is never for sale, because an index whose order can be bought is worth nothing to the reader and therefore nothing to you.</p>
  </section>
</div>

<div class="bleed bleed-green"><div class="wrap">
  <div class="figures">
    <div class="figure"><span class="v">0%</span><span class="k">commission on your sales</span></div>
    <div class="figure"><span class="v">0</span><span class="k">affiliate links in listings</span></div>
    <div class="figure"><span class="v">100%</span><span class="k">of paid placement labelled</span></div>
    <div class="figure"><span class="v">{money(SITE["price_entry"])}</span><span class="k">entry listing, per month</span></div>
  </div>
</div></div>

<div class="wrap">
  <div class="rule"><h2>What you can buy</h2><span class="n">all of it labelled, all of it cancellable</span></div>
  <dl class="spec">
    <div><dt>A listing</dt><dd>Your store on the index with a page you control the facts of, from {money(SITE["price_entry"])} a month. This is not advertising \u2014 it is the product \u2014 but it is the thing most people are asking about. <a href="/pricing/">See the tiers \u2192</a></dd></div>
    <div><dt>Sponsored placement</dt><dd>A fixed slot on a category, type or brand page, marked <em>Sponsored</em> in the same type size as everything around it. It sits outside the ranked list rather than inside it, so it never displaces a result a reader was looking for.</dd></div>
    <div><dt>Journal sponsorship</dt><dd>A single labelled sponsor per article, named at the top. No sponsored articles, no paid mentions inside the text, and sponsors see no copy before it is published.</dd></div>
    <div><dt>Feed sponsorship</dt><dd>Attribution in the open data feeds and their documentation, for tools and services built on top of the index.</dd></div>
  </dl>

  <div class="rule"><h2>What you cannot buy</h2><span class="n">at any price</span></div>
  <div class="split pair">
    <div>
      <h3>Not for sale</h3>
      <ul>
        <li>Position in the index, or in any ranked or sorted list.</li>
        <li>Removal of a competitor, or of a correction about you.</li>
        <li>A verification mark. Verification is a check we perform, not a badge we sell.</li>
        <li>Editorial coverage, or changes to an article after publication.</li>
        <li>An unlabelled placement of any kind.</li>
      </ul>
    </div>
    <div>
      <h3>Always true</h3>
      <ul>
        <li>Paid placement is labelled where a reader sees it, not only in a policy page.</li>
        <li>Advertisers get the same record accuracy as everyone else, no better.</li>
        <li>Cancel any time; nothing here runs on a term.</li>
        <li>Your data stays exportable, including on the way out.</li>
      </ul>
    </div>
  </div>

  <div class="rule"><h2>Who reads this</h2></div>
  <p>Two audiences, reading the same pages. Shoppers arriving on a category, type or brand page with a specific thing in mind. And machines \u2014 the crawlers and assistants that read this index as a source, which is the whole reason it is built the way it is. We publish real figures rather than a media kit: the index currently holds <b>{len(STORES)}</b> store{"s" if len(STORES)!=1 else ""}, <b>{len(PRODUCTS)}</b> listings and <b>{len(TYPES)}</b> product types, compiled {TODAY}. When those numbers are small, they will say so.</p>

  <div class="ledge">
    <h2>Interested?</h2>
    <p>Tell us which store, which category, and what you are trying to achieve. If a listing would serve you better than a placement, we will say so.</p>
    <span class="after"><a href="/contact/">Get in touch</a><a href="/pricing/">See the tiers</a><a href="/join/">Apply to list</a></span>
  </div>
</div></main>
{footer()}"""
    return write("advertise/index.html", head(f"Advertise on {BRAND}",
        "Labelled placements only. Ranking is never for sale. What you can buy on the index, what you cannot, and the real figures.",
        "/advertise/", ld=ld_crumbs(trail)) + body)

FAQS = [
 ("What is Commerce Plugs?",
  "Commerce Plugs is an index of independent online stores. You search it, find the product you want, and then buy it on the seller's own website. It is not a marketplace: there is no checkout here, no commission is taken on any sale, and every listing links directly to the store that sells it."),
 ("Do you sell anything directly?",
  "No. We never handle payment and we hold no inventory. Every link goes to the independent store that sells the item, and you buy from them under their terms, with their returns policy and their customer service."),
 ("Do you take a commission or add a markup?",
  "No. We take no commission, no referral fee and no cut of any sale, and we run no affiliate links inside listings. Nothing on the index is marked up to pay us. Stores pay a flat monthly fee to be listed, and that is the entire business model."),
 ("How do you decide what order things appear in?",
  "Position on the index is not for sale at any price. Paid placement exists, but it sits outside the ranked lists and is labelled as sponsored where you see it, in the same type size as everything around it."),
 ("Where do your prices come from, and are they current?",
  "Prices, stock and specifications are read from each seller's own public catalog and carry the date we read them. We do not retype or adjust them. Because a store can change a price at any time, you should always check the figure on the store's own page before you buy."),
 ("What does it mean when a field says 'not verified'?",
  "It means exactly that: we have not confirmed it with the store. We publish a blank rather than a plausible guess. Likewise a store that has not connected a product feed shows no prices at all, rather than estimated ones."),
 ("How does a store get listed?",
  "A store applies, and every applicant is checked by hand. We confirm that it is an independent seller rather than a marketplace reseller, that it controls its own checkout, that its products and prices are real, and that it ships somewhere reliably. Listing starts at $19.99 a month with no contract and no minimum term."),
 ("Is there a free listing?",
  "No. There is no free tier, because a free listing that nobody maintains is the thing that does not work — it goes stale, and a stale record is worse than no record."),
 ("Can I use your data?",
  "Yes. The store and product feeds are public, documented and licensed CC-BY-4.0, so you can read and reuse them with attribution. There is also an MCP server definition, so an AI assistant can query the index directly rather than relying on having crawled it."),
 ("How do I correct something that is wrong about my store?",
  "Tell us and we will fix it and re-date the record. You do not have to be a paying listing to get an error corrected, and you do not have to be the store owner to report one."),
]

def page_faq():
    trail = [("Home","/"),("Questions",None)]
    items = "".join(
        f'<div class="qa" id="q{i+1}"><h2>{e(q)}</h2><p>{e(a)}</p></div>'
        for i, (q, a) in enumerate(FAQS))
    ld = [ld_crumbs(trail),
          {"@context":"https://schema.org","@type":"FAQPage",
           "mainEntity":[{"@type":"Question","name":q,
                          "acceptedAnswer":{"@type":"Answer","text":a}} for q, a in FAQS]},
          {"@context":"https://schema.org","@type":"WebPage","@id":BASE+"/faq/#page",
           "name":f"Questions about {BRAND}","url":BASE+"/faq/",
           "speakable":{"@type":"SpeakableSpecification","cssSelector":[".qa h2",".qa p"]}}]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap narrow">
  <section class="state" style="padding:34px 0 26px">
    <p class="label">Questions</p>
    <h1>Straight answers.</h1>
    <p>Each answer below is written to stand on its own, so it reads correctly whether you are scanning the page, hearing it read aloud, or getting it quoted back to you by an assistant.</p>
  </section>
  <div class="rule" style="margin-top:0"><h2>Common questions</h2><span class="n">{len(FAQS)} answered</span></div>
  <div class="faq">{items}</div>
  <div class="ledge">
    <h2>Something not answered here?</h2>
    <p>Ask a person. Corrections about a store are treated as urgent.</p>
    <span class="after"><a href="/contact/">Contact</a><a href="/how-it-works/">How it works</a><a href="/about/">About</a></span>
  </div>
</div></main>
{footer()}"""
    return write("faq/index.html", head(f"Questions about {BRAND}",
        "What the index is, how prices are sourced, what 'not verified' means, how stores get listed, and what is never for sale.",
        "/faq/", ld=ld) + body)

def _stats_block():
    """Real figures, computed at build time. A data post that hardcodes its
    numbers goes stale silently; this one cannot."""
    pr = sorted(float(x["price"]) for x in PRODUCTS if x.get("price"))
    if not pr: return ""
    mid = pr[len(pr)//2]
    return f"""<div class="figures" style="margin:20px 0 26px">
  <div class="figure"><span class="v">{len(PRODUCTS)}</span><span class="k">priced listings read</span></div>
  <div class="figure"><span class="v">{len(TYPES)}</span><span class="k">product types</span></div>
  <div class="figure"><span class="v">{money_mono(mid)}</span><span class="k">median listing</span></div>
  <div class="figure"><span class="v">{money_mono(pr[0])}\u2013{money_mono(pr[-1])}</span><span class="k">full range</span></div>
</div>"""

def _types_block():
    rows = ""
    for k, v in list(TYPES.items())[:12]:
        pr = sorted(float(x["price"]) for x in v["items"] if x.get("price"))
        if not pr: continue
        rows += (f'<tr><td class="ix-n">{len(v["items"]):02d}</td>'
                 f'<td class="nm"><a href="/t/{k}/">{e(v["name"])}</a></td>'
                 f'<td class="num">{money_mono(pr[0])}</td>'
                 f'<td class="num">{money_mono(pr[len(pr)//2])}</td>'
                 f'<td class="num">{money_mono(pr[-1])}</td></tr>')
    return (f'<table class="register" style="margin:18px 0 24px"><thead><tr><th>n</th><th>Type</th>'
            f'<th class="num">Lowest</th><th class="num">Median</th><th class="num">Highest</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>')

def _brands_block():
    return ('<div class="index-list" style="margin:16px 0 24px">' +
            "".join(index_entry(v["name"], f"/b/{k}/", len(v["items"])) for k, v in BRANDS.items()) +
            "</div>")

BLOCKS = {"stats": _stats_block, "types": _types_block, "brands": _brands_block}

def render_body(body):
    out = ""
    for kind, val in body:
        if kind == "p":    out += f"<p>{e(val)}</p>"
        elif kind == "h2": out += f'<h2 style="margin-top:1.8rem">{e(val)}</h2>'
        elif kind == "h3": out += f'<h3 style="margin-top:1.2rem">{e(val)}</h3>'
        elif kind == "list": out += "<ul>" + "".join(f"<li>{e(x)}</li>" for x in val) + "</ul>"
        elif kind in BLOCKS: out += BLOCKS[kind]()
    return out

def page_post(post):
    trail = [("Home","/"),("Journal","/journal/"),(post["title"],None)]
    others = [x for x in JOURNAL if x["slug"] != post["slug"]][:2]
    more = "".join(
        f'<div class="card"><p class="label">{e(x["kicker"])}</p>'
        f'<h3 style="margin:.2rem 0 .4rem"><a href="/journal/{x["slug"]}/">{e(x["title"])}</a></h3>'
        f'<p class="sm muted" style="margin:0">{e(x["summary"])}</p></div>' for x in others)
    ld = [ld_crumbs(trail),
          {"@context":"https://schema.org","@type":"Article",
           "headline":post["title"],"description":post["summary"],
           "datePublished":post["date"],"dateModified":post.get("updated", post["date"]),
           "url":f"{BASE}/journal/{post['slug']}/",
           "mainEntityOfPage":{"@type":"WebPage","@id":f"{BASE}/journal/{post['slug']}/"},
           "image":f"{BASE}/assets/og/default.jpg",
           "keywords":", ".join(post.get("tags", [])),
           "author":{"@type":"Organization","name":BRAND,"url":BASE+"/"},
           "publisher":{"@id":BASE+"/#org"},
           "isAccessibleForFree":True,
           "speakable":{"@type":"SpeakableSpecification","cssSelector":[".post h1",".post > p"]}}]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap narrow">
  <p class="orient"><b>{e(post["kicker"])}</b><span class="sep">/</span>
    published <b>{e(post["date"])}</b>
    {f'<span class="sep">/</span>updated <b>{e(post["updated"])}</b>' if post.get("updated") and post["updated"] != post["date"] else ""}
    {'<span class="sep">/</span>figures recomputed at build' if post.get("data_post") else ""}</p>
  <article class="post">
    <h1 style="margin:28px 0 .8rem">{e(post["title"])}</h1>
    <p style="font-size:1.15rem;color:var(--ink-2);max-width:60ch">{e(post["summary"])}</p>
    <hr>
    {render_body(post["body"])}
  </article>
  {f'<div class="rule"><h2>Also in the journal</h2></div><div class="grid g2" style="gap:18px;margin-top:16px">{more}</div>' if more else ""}
</div></main>
{footer()}"""
    return write(f"journal/{post['slug']}/index.html",
        head(f"{post['title']} | {BRAND}", post["summary"][:158], f"/journal/{post['slug']}/", ld=ld) + body)

def page_journal():
    trail = [("Home","/"),("Journal",None)]
    rows = "".join(
        f"""<article class="jrow">
  <p class="label">{e(x["kicker"])} <span class="muted" style="font-style:normal">\u00b7 {e(x["date"])}</span></p>
  <h2><a href="/journal/{x["slug"]}/">{e(x["title"])}</a></h2>
  <p>{e(x["summary"])}</p>
  <p class="rail">{" \u00b7 ".join(e(t) for t in x.get("tags", []))}</p>
</article>""" for x in JOURNAL)
    ld = [ld_crumbs(trail),
          {"@context":"https://schema.org","@type":"Blog","name":f"{BRAND} Journal","url":BASE+"/journal/",
           "publisher":{"@id":BASE+"/#org"},
           "blogPost":[{"@type":"BlogPosting","headline":x["title"],"url":f"{BASE}/journal/{x['slug']}/",
                        "datePublished":x["date"],"description":x["summary"]} for x in JOURNAL]}]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap narrow">
  <p class="orient"><b>{len(JOURNAL)}</b> article{"s" if len(JOURNAL)!=1 else ""}<span class="sep">/</span>
    figures drawn from the index itself<span class="sep">/</span>
    <a href="/journal/feed.xml">RSS</a></p>
  <section class="state" style="padding:34px 0 26px">
    <p class="label">Journal</p>
    <h1>Written from the index, not around it.</h1>
    <p>No tips listicles. What gets published here is either derived from data this index actually holds, or an argument about machine-readable commerce that we can back with a test you can run yourself.</p>
  </section>
  <div class="rule" style="margin-top:0"><h2>Articles</h2><span class="n">newest first</span>
    <a class="more" href="/journal/feed.xml">RSS \u2192</a></div>
  <div class="jlist">{rows}</div>
</div></main>
{footer()}"""
    return write("journal/index.html", head(f"Journal | {BRAND}",
        "Data drawn from the index, and the argument for machine-readable commerce. No tips listicles.",
        "/journal/", ld=ld) + body)

# ---------------------------------------------------------------- machine
def machine_files():
    out = []
    stores_feed = {"generated_at": TODAY + "T00:00:00Z", "schema": BASE + "/feeds/README.md",
        "license": "CC-BY-4.0", "count": len(STORES),
        "notes": "Unconfirmed fields are null, never estimated. No placeholder records.",
        "stores": [{"id": s["slug"], "name": s["name"], "url": s["url"], "page": f"{BASE}/stores/{s['slug']}/",
                    "description": s.get("summary"), "categories": s.get("categories",[]),
                    "ships_from": s.get("ships_from"), "ships_to": s.get("ships_to",[]),
                    "currency": s.get("currency"),
                    "listing_status": s.get("listing_status","pending_verification"),
                    "catalog_status": s.get("catalog_status","not_connected"),
                    "listings": len([x for x in PRODUCTS if x["store"]==s["slug"]]),
                    "added": s.get("added"), "last_verified": s.get("verified")} for s in STORES]}
    out.append(write("feeds/stores.json", json.dumps(stores_feed, indent=2)))

    prod_feed = {"generated_at": TODAY + "T00:00:00Z", "schema": BASE + "/feeds/README.md",
        "license": "CC-BY-4.0", "count": len(PRODUCTS),
        "notes": "Only listings from stores with a connected catalog feed. No generated or estimated entries.",
        "products": [{"item_id": p["id"], "title": p["title"], "description": p.get("blurb",""),
                      "url": p["url"], "brand": p.get("brand",""), "seller_name": STOREBY.get(p["store"],{}).get("name",""),
                      "seller_page": f"{BASE}/stores/{p['store']}/", "image_url": p.get("image"),
                      "availability": p.get("availability","in_stock"),
                      "price": f"{float(p['price']):.2f} {p.get('currency','USD')}",
                      "sku": p.get("sku"), "category": p.get("category"), "last_verified": TODAY} for p in PRODUCTS]}
    out.append(write("feeds/products.json", json.dumps(prod_feed, indent=2)))

    # ACP-shaped TSV
    cols = ["item_id","title","description","url","brand","seller_name","image_url","availability","price"]
    rows = ["\t".join(cols)]
    for p in PRODUCTS:
        rows.append("\t".join([p["id"], p["title"], p.get("blurb",""), p["url"], p.get("brand",""),
            STOREBY.get(p["store"],{}).get("name",""), p.get("image") or "", p.get("availability","in_stock"),
            f"{float(p['price']):.2f} {p.get('currency','USD')}"]))
    out.append(write("feeds/products.tsv", "\n".join(rows) + "\n"))

    out.append(write("feeds/README.md", f"""# {BRAND} open feeds

Public, documented, free to read and re-use under CC-BY-4.0.

| File | What it is |
|---|---|
| `stores.json` | Every verified store: name, URL, categories, shipping, `last_verified`. |
| `products.json` | Every listing: title, description, price with currency, availability, seller, `last_verified`. |
| `products.tsv` | The same catalog in the 9-column shape used by the Agentic Commerce Protocol product feed spec. |

Every record carries `last_verified`. A field we have not confirmed with the
store is published as `null`, never estimated, so a missing value means unknown
rather than zero. These feeds contain no placeholder or generated records: a
store that has not connected a catalog feed contributes no products.

Attribution: {BRAND} ({BASE}).
"""))

    # search index
    idx = [{"t": p["title"], "u": p["url"], "p": p["price"], "c": p.get("currency","USD"),
            "s": STOREBY.get(p["store"],{}).get("name",""), "sl": p["store"],
            "cat": p.get("category"), "sub": p.get("subcategory",""), "sku": p.get("sku",""),
            "b": p.get("brand",""), "img": p.get("image"), "d": p.get("dimensions"), "f": p.get("finish")} for p in PRODUCTS]
    out.append(write("search-index.json", json.dumps({"generated": TODAY, "items": idx}, separators=(",",":"))))

    out.append(write(".well-known/mcp/server.json", json.dumps({
        "name": "commerce-plugs-index",
        "version": "1.0.0",
        "description": f"Query {BRAND}, an index of verified independent online stores. Read-only. Every record carries a verification date.",
        "websiteUrl": BASE + "/",
        "capabilities": {"tools": True},
        "tools": [
            {"name":"search_products","description":"Search listings across every independent store in the index.",
             "inputSchema":{"type":"object","properties":{"query":{"type":"string"},"category":{"type":"string"},
               "max_price":{"type":"number"},"ships_to":{"type":"string"},"limit":{"type":"integer","default":20}},"required":["query"]}},
            {"name":"search_stores","description":"Find independent stores by category, country or what they sell.",
             "inputSchema":{"type":"object","properties":{"query":{"type":"string"},"category":{"type":"string"},
               "ships_to":{"type":"string"},"limit":{"type":"integer","default":20}}}},
            {"name":"get_store","description":"Full record for one store, including catalog and verification date.",
             "inputSchema":{"type":"object","properties":{"store_id":{"type":"string"}},"required":["store_id"]}},
            {"name":"list_categories","description":"All categories with store and listing counts.",
             "inputSchema":{"type":"object","properties":{}}}
        ],
        "dataFeeds": [{"type":"stores","url":BASE+"/feeds/stores.json"},
                      {"type":"products","url":BASE+"/feeds/products.json"},
                      {"type":"products-tsv","url":BASE+"/feeds/products.tsv"}]
    }, indent=2)))

    # robots — permissive on purpose
    out.append(write("robots.txt", f"""# {BRAND} — we are a corpus, not a walled garden. AI crawlers welcome.
User-agent: *
Allow: /

User-agent: Googlebot
Allow: /
User-agent: Bingbot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: GPTBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: CCBot
Allow: /

Sitemap: {BASE}/sitemap.xml
"""))

    cat_lines = "\n".join(f"- [{c['name']}]({BASE}/c/{c['slug']}/): {c['blurb']}" for c in CATS)
    type_lines = "\n".join(f"- [{v['name']}]({BASE}/t/{k}/): {len(v['items'])} listings" for k, v in TYPES.items()) or "- None yet."
    brand_lines = "\n".join(f"- [{v['name']}]({BASE}/b/{k}/): {len(v['items'])} listings" for k, v in BRANDS.items()) or "- None yet."
    store_lines = "\n".join(
        f"- [{s['name']}]({BASE}/stores/{s['slug']}/) — independent store, sells direct at {s['url']}. "
        f"Categories: {', '.join(CATBY[c]['name'] for c in s.get('categories',[]) if c in CATBY) or 'unclassified'}. "
        f"Listings published: {len([x for x in PRODUCTS if x['store']==s['slug']])}. "
        f"{'Verified ' + s['verified'] if s.get('verified') else 'Listing pending verification; shipping, currency and catalog not yet confirmed.'}"
        for s in STORES) or "- No stores published yet."
    out.append(write("llms.txt", f"""# {BRAND}

> {SITE['tagline']} {SITE['pitch']} An index of verified independent online stores. Every listing links to the seller's own site; we take no commission and host no checkout.

## Open data
- Store feed (JSON): {BASE}/feeds/stores.json
- Product feed (JSON): {BASE}/feeds/products.json
- Product feed (TSV, ACP column shape): {BASE}/feeds/products.tsv
- Feed documentation: {BASE}/feeds/README.md
- MCP server definition: {BASE}/.well-known/mcp/server.json
- Search index (JSON): {BASE}/search-index.json

## Stores
{store_lines}

## Categories
{cat_lines}

## Product types
{type_lines}

## Brands carried
{brand_lines}

## Reference
- Questions and answers: {BASE}/faq/
- Journal (data drawn from the index): {BASE}/journal/
- Journal feed (RSS): {BASE}/journal/feed.xml
- Editorial standards and what we refuse to publish: {BASE}/journal/how-we-verify-a-store/
- Contact: {BASE}/contact/
- Advertising policy: {BASE}/advertise/

## For brands
- Why list: {BASE}/for-brands/
- Pricing, from ${SITE['price_entry']}/mo, no contract: {BASE}/pricing/
- Apply: {BASE}/join/

## Notes for retrieval
Pages are server-rendered; no content on this site requires JavaScript to read.
Prices, when published, are written in readable text as well as marked up.

Records carry a `last_verified` date. Where a field has not been confirmed with
the store it is published as null or "not verified" rather than estimated, so an
absent value here means unknown, not zero. This index contains no generated or
placeholder product data: a store with no connected catalog feed shows no
listings. Store counts and listing counts in this file are literal.

Publisher: {SITE['publisher']} ({SITE['publisher_url']}).
"""))

    urls = ["/", "/contents/", "/stores/", "/search/", "/for-brands/", "/pricing/",
            "/how-it-works/", "/join/", "/about/", "/contact/", "/advertise/", "/faq/", "/journal/"]
    urls += [f"/journal/{x['slug']}/" for x in JOURNAL]
    urls += [f"/c/{c['slug']}/" for c in CATS]
    urls += [f"/t/{k}/" for k in TYPES]
    urls += [f"/b/{k}/" for k in BRANDS]
    urls += [f"/stores/{s['slug']}/" for s in STORES]
    body = "".join(
        f"<url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod>"
        f"<priority>{'1.0' if u=='/' else '0.8' if u.startswith('/c/') or u.startswith('/stores/') else '0.6'}</priority></url>"
        for u in urls)
    out.append(write("sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + body + "</urlset>"))

    out.append(write("site.webmanifest", json.dumps({
        "name": BRAND, "short_name": SITE["short"],
        "description": SITE["pitch"], "start_url": "/", "scope": "/",
        "display": "standalone", "background_color": "#FFFFFF", "theme_color": "#6E3BFF",
        "icons": [{"src": "/assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "/assets/icons/icon.svg", "sizes": "any", "type": "image/svg+xml"}],
    }, indent=2)))

    def rfc822(d):
        import datetime as _dt
        return _dt.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
    items = "".join(
        f"<item><title>{html.escape(x['title'])}</title>"
        f"<link>{BASE}/journal/{x['slug']}/</link>"
        f"<guid isPermaLink=\"true\">{BASE}/journal/{x['slug']}/</guid>"
        f"<pubDate>{rfc822(x['date'])}</pubDate>"
        f"<description>{html.escape(x['summary'])}</description>"
        + "".join(f"<category>{html.escape(t)}</category>" for t in x.get("tags", []))
        + "</item>" for x in JOURNAL)
    out.append(write("journal/feed.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
        f"<title>{html.escape(BRAND)} Journal</title><link>{BASE}/journal/</link>"
        f"<description>{html.escape(SITE['pitch'])}</description><language>en-us</language>"
        f'<atom:link href="{BASE}/journal/feed.xml" rel="self" type="application/rss+xml"/>'
        f"{items}</channel></rss>"))

    out.append(write("CNAME", SITE["domain"] + "\n"))
    out.append(write(".nojekyll", ""))
    return out

# ---------------------------------------------------------------- run
def main():
    made = []
    made.append(page_home())
    made.append(page_stores())
    for s in STORES: made.append(page_store(s))
    for c in CATS: made.append(page_category(c))
    made.append(page_indexes())
    for k, v in TYPES.items():  made.append(page_facet("t", k, v))
    for k, v in BRANDS.items(): made.append(page_facet("b", k, v))
    made.append(page_search())
    made.append(page_for_brands())
    made.append(page_pricing())
    made.append(page_how())
    made.append(page_join())
    made.append(page_thanks())
    made.append(page_about())
    made.append(page_contact())
    made.append(page_advertise())
    made.append(page_faq())
    made.append(page_journal())
    for post in JOURNAL: made.append(page_post(post))
    made.append(page_404())
    made += machine_files()
    print(f"built {len(made)} files")
    for m in made: print("  " + m)

if __name__ == "__main__":
    main()
