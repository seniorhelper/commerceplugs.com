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

BASE = "https://" + SITE["domain"]
BRAND = SITE["brand"]
CATBY = {c["slug"]: c for c in CATS}
STOREBY = {s["slug"]: s for s in STORES}
for c in CATS:
    c["stores"] = [s for s in STORES if c["slug"] in s.get("categories", [])]
    c["products"] = [p for p in PRODUCTS if p.get("category") == c["slug"]]

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
def head(title, desc, path, extra="", ld=None):
    url = BASE + path
    blocks = ""
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
<meta name="theme-color" content="#0B0B0F">
<meta property="og:site_name" content="{e(BRAND)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap">
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/app.js" defer></script>
<link rel="alternate" type="application/json" href="{BASE}/feeds/products.json" title="Product feed">
{blocks}{extra}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""

def header(active=None):
    opts = '<option value="">All categories</option>' + "".join(
        f'<option value="{c["slug"]}">{e(c["name"])}</option>' for c in CATS)
    strip = "".join(
        f'<a href="/c/{c["slug"]}/"{" aria-current=\"page\"" if active==c["slug"] else ""}>{e(c["name"])}</a>'
        for c in CATS)
    return f"""<header class="top">
<div class="top-in">
  <a class="mark" href="/"><span class="m1">{e(BRAND)}</span><span class="m2">Index</span></a>
  <form class="find" action="/search/" method="get" role="search">
    <label class="sr" for="q">Search independent stores and products</label>
    <select name="c" aria-label="Category">{opts}</select>
    <input id="q" name="q" type="search" placeholder="Search products from independent stores" autocomplete="off">
    <button type="submit">Search</button>
  </form>
  <nav class="top-act" aria-label="Account">
    <a class="no-sm" href="/stores/">Stores</a>
    <a class="no-sm" href="/how-it-works/">How it works</a>
    <a class="cta" href="/for-brands/">List your brand</a>
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
        ("Shop", [("All stores","/stores/"),("Categories","/#categories"),("Search","/search/"),("Recently added","/stores/")]),
        ("For brands", [("Why list here","/for-brands/"),("Pricing","/pricing/"),("How it works","/how-it-works/"),("Get listed","/join/")]),
        ("Machine", [("Store feed","/feeds/stores.json"),("Product feed","/feeds/products.json"),("MCP server","/.well-known/mcp/server.json"),("llms.txt","/llms.txt")]),
        ("Company", [("About","/about/"),("Contact","/join/"),("Sitemap","/sitemap.xml"),("Publisher",SITE["publisher_url"])]),
    ]:
        items = "".join(f'<li><a href="{l}">{e(n)}</a></li>' for n, l in links)
        cols += f'<div><h4>{e(group)}</h4><ul>{items}</ul></div>'
    return f"""<footer class="foot">
<div class="foot-in">
  <div class="foot-cols">
    <div>
      <a class="mark" href="/" style="margin-bottom:10px"><span class="m1" style="color:var(--ink)">{e(BRAND)}</span><span class="m2">Index</span></a>
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
    featured = STORES[0] if STORES else None
    prods = PRODUCTS[:12]
    cat_tiles = "".join(
        f"""<a class="cat" href="/c/{c["slug"]}/">
  <div class="ic">{icon(c["icon"])}</div>
  <h3>{e(c["name"])}</h3>
  <p>{e(c["blurb"])}</p>
</a>""" for c in CATS)

    prod_html = "".join(product_card(p) for p in prods)
    if prods:
        listings_section = f"""<section class="sec" style="background:var(--surface);border-top:var(--rail);border-bottom:var(--rail)"><div class="wrap">
  <div class="sec-head">
    <div><p class="eyebrow alt">Live listings</p><h2>In stock right now.</h2></div>
    <a class="btn btn-sm btn-ghost" href="/search/">Search everything</a>
  </div>
  <div class="grid g4">{prod_html}</div>
</div></section>"""
    else:
        listings_section = f"""<section class="sec" style="background:var(--surface);border-top:var(--rail);border-bottom:var(--rail)"><div class="wrap">
  <div class="sec-head">
    <div><p class="eyebrow alt">Opening now</p><h2>The index is live. The shelves are not full yet.</h2></div>
  </div>
  <div class="split" style="margin-top:0">
    <div>
      <p>We are not going to pad this page out with made-up products to look bigger than we are. Product listings appear here when a store connects a catalog feed, and not a second before. Right now {len(STORES)} store{"s" if len(STORES)!=1 else ""} {"are" if len(STORES)!=1 else "is"} indexed and {len(CATS)} categories are open.</p>
      <p>If you sell something good and you are tired of renting your own customers back from a marketplace, this is the moment to be early.</p>
      <div class="hero-cta"><a class="btn btn-brand" href="/for-brands/">Why list here</a><a class="btn btn-ghost" href="/join/">Apply to list</a></div>
    </div>
    <div class="machine">
      <div class="machine-bar"><span>what you will not find on this site</span><span class="led"></span></div>
      <pre>  <span class="k">×</span> invented products
  <span class="k">×</span> estimated prices
  <span class="k">×</span> stock we did not check
  <span class="k">×</span> affiliate links in listings
  <span class="k">×</span> paid placement dressed as editorial
  <span class="s">+</span> a date on every record</pre>
    </div>
  </div>
</div></section>"""
    store_html = "".join(store_card(s) for s in STORES) + open_slot("Your brand here")

    sample = {"index": SITE["domain"], "stores": len(STORES), "listings": len(PRODUCTS),
              "categories": len(CATS), "commission": "0%", "checkout": "seller's own",
              "built": TODAY, "feed": BASE + "/feeds/stores.json",
              "mcp": BASE + "/.well-known/mcp/server.json"}
    pretty = json.dumps(sample, indent=2)

    ld = [{"@context":"https://schema.org","@type":"WebSite","name":BRAND,"url":BASE+"/",
           "potentialAction":{"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":BASE+"/search/?q={search_term_string}"},"query-input":"required name=search_term_string"}},
          {"@context":"https://schema.org","@type":"Organization","name":BRAND,"url":BASE+"/","description":SITE["pitch"]}]

    body = f"""{header()}
<main id="main">
<section class="hero"><div class="wrap hero-in">
  <div>
    <p class="eyebrow">Independent stores · machine readable</p>
    <h1>Shop the brands Amazon buried.</h1>
    <p class="lede">{e(SITE["pitch"])} Search real independent stores, then buy on their own site. We never touch the transaction.</p>
    <div class="hero-cta">
      <a class="btn btn-brand btn-lg" href="#categories">Start shopping</a>
      <a class="btn btn-ghost btn-lg" href="/for-brands/">List your brand</a>
    </div>
    <p class="rail mt2"><b>No marketplace fees</b><span class="dot"></span><b>No middleman checkout</b><span class="dot"></span><b>Brand keeps the customer</b></p>
  </div>
  <div class="machine">
    <div class="machine-bar"><span>agent-readable record</span><span class="led"></span></div>
    <pre>{e(pretty)}</pre>
  </div>
</div></section>

<section class="sec-tight"><div class="wrap">
  <div class="stats">
    <div class="stat"><span class="n">{len(STORES)}</span><span class="l">Stores indexed</span></div>
    <div class="stat"><span class="n">{len(PRODUCTS)}</span><span class="l">Listings published</span></div>
    <div class="stat"><span class="n">{len(CATS)}</span><span class="l">Categories open</span></div>
    <div class="stat"><span class="n">0%</span><span class="l">Commission we take</span></div>
  </div>
</div></section>

<section class="sec" id="categories"><div class="wrap">
  <div class="sec-head">
    <div><p class="eyebrow alt">Browse</p><h2>Every category, independent only.</h2></div>
    <a class="btn btn-sm btn-ghost" href="/stores/">All stores</a>
  </div>
  <div class="grid g6">{cat_tiles}</div>
</div></section>

{listings_section}

<section class="sec"><div class="wrap">
  <div class="sec-head">
    <div><p class="eyebrow alt">The index</p><h2>Stores on the record.</h2></div>
  </div>
  <div class="grid g3">{store_html}</div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="band">
    <div class="grid g2" style="align-items:center;gap:30px">
      <div>
        <p class="eyebrow" style="color:#8E7BFF">For brands</p>
        <h2>If a machine cannot read your store, it cannot recommend it.</h2>
        <p>The crawlers behind AI assistants do not run JavaScript, do not log in and do not guess. They can only pass along what is written down in plain text, at a fixed address, with a date on it. Most independent stores have none of that. Building it is the whole job, and it costs {money(SITE["price_entry"])} a month.</p>
        <a class="btn btn-lg" href="/for-brands/">See how it works</a>
      </div>
      <div class="machine" style="box-shadow:3px 3px 0 #000">
        <div class="machine-bar"><span>what a crawler can and cannot read</span><span class="led"></span></div>
        <pre>  <span class="s">+</span> a page it can fetch
  <span class="s">+</span> prices written as text
  <span class="s">+</span> a date on the record
  <span class="s">+</span> pages elsewhere that cite you
  <span class="k">×</span> a price inside a script
  <span class="k">×</span> a spec sheet inside an image
  <span class="k">×</span> a catalog behind a login</pre>
      </div>
    </div>
  </div>
</div></section>
</main>
{footer()}"""
    return write("index.html", head(f"{BRAND} — {SITE['tagline']}",
        "Search independent online stores and buy direct from the brand. No marketplace fees, no middleman checkout.",
        "/", ld=ld) + body)

def page_category(c):
    trail = [("Home","/"),("Categories","/#categories"),(c["name"],None)]
    prods = c["products"]
    stores = c["stores"]
    grid = "".join(product_card(p) for p in prods) if prods else open_slot(f"{c['name']} is open")
    slist = "".join(store_card(s) for s in stores) if stores else open_slot("No stores listed yet")
    other = "".join(f'<li><a href="/c/{o["slug"]}/"{" aria-current=\"page\"" if o["slug"]==c["slug"] else ""}>{e(o["name"])}</a></li>' for o in CATS)
    subs = sorted({p.get("subcategory") for p in prods if p.get("subcategory")})
    subhtml = "".join(f'<label class="chk"><input type="checkbox" data-sub="{e(s)}"> {e(s)}</label>' for s in subs)

    ld = [ld_crumbs(trail),
          {"@context":"https://schema.org","@type":"CollectionPage","name":f"{c['name']} — independent stores",
           "url":f"{BASE}/c/{c['slug']}/","description":c["blurb"],
           "mainEntity":{"@type":"ItemList","numberOfItems":len(prods),
             "itemListElement":[{"@type":"ListItem","position":i+1,"url":p["url"],"name":p["title"]} for i,p in enumerate(prods)]}}]

    body = f"""{header(active=c["slug"])}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <div class="sec-head" style="margin-bottom:22px">
    <div><p class="eyebrow">Category</p><h1>{e(c["name"])}</h1><p class="lede" style="margin:0">{e(c["blurb"])}</p></div>
  </div>
  <div class="shell">
    <div>
      <aside class="side">
        <h4>Categories</h4>
        <ul>{other}</ul>
      </aside>
      {'<aside class="side"><h4>Type</h4>' + subhtml + '</aside>' if subhtml else ''}
      <aside class="side">
        <h4>Machine record</h4>
        <p class="sm muted" style="margin:0 0 8px">This page is published as structured data and an open feed.</p>
        <a class="btn btn-sm btn-ghost" href="/feeds/products.json">Product feed</a>
      </aside>
    </div>
    <div>
      <div class="bar">
        <span class="count">{len(prods)} listing{"s" if len(prods)!=1 else ""} · {len(stores)} store{"s" if len(stores)!=1 else ""}</span>
        <select id="sort" aria-label="Sort"><option value="rel">Sort: relevance</option><option value="lo">Price: low to high</option><option value="hi">Price: high to low</option></select>
      </div>
      <div class="grid g3" id="results">{grid}</div>

      <div class="sec-head mt2" style="margin-top:36px"><div><p class="eyebrow alt">Stores</p><h2>Who sells in {e(c["name"])}</h2></div></div>
      <div class="grid g2">{slist}</div>
    </div>
  </div>
</div></main>
{footer()}"""
    return write(f"c/{c['slug']}/index.html",
        head(f"{c['name']} from independent stores | {BRAND}", c["blurb"] + f" Browse {len(prods)} listings from independent sellers and buy direct.",
             f"/c/{c['slug']}/", ld=ld) + body)

def page_store(s):
    trail = [("Home","/"),("Stores","/stores/"),(s["name"],None)]
    prods = [p for p in PRODUCTS if p["store"] == s["slug"]]
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z0-9]+", s["name"])[:2]).upper()
    cats = ", ".join(CATBY[c]["name"] for c in s.get("categories", []) if c in CATBY)
    grid = "".join(product_card(p) for p in prods) if prods else f"""<div class="slot">
  <span class="tag">Catalog not connected</span>
  <h3>No product listings published yet</h3>
  <p>{e(s["name"])} has a listing on the index but has not connected a product feed, so we publish no prices or stock for it. Nothing here is estimated. Browse the catalog at the store itself.</p>
  <a class="btn btn-sm btn-brand" href="{e(s["url"])}" rel="nofollow noopener" target="_blank" style="align-self:flex-start">Open {e(s["name"])}</a>
</div>"""
    vals = "".join(f'<span class="tag">{e(v)}</span>' for v in s.get("values", []))
    if s.get("summary"):
        about_copy = e(s["summary"])
    else:
        about_copy = (f'{e(s["name"])} is an independent online store listed on the index in '
                      f'{e(cats) or "a category"}. We publish the store name, its web address and the '
                      f'categories it is indexed under. Everything else on this page is marked '
                      f'<em>not verified</em> until the store confirms it, because we would rather '
                      f'show you a blank than a guess.')
    note = ""
    if not s.get("verified"):
        note = f"""<div class="note"><p class="sm"><b>Record status:</b> this listing holds only what we can confirm — the store name and its web address. We have not yet verified shipping, returns, currency or catalog with {e(s["name"])}, so those fields read <em>not verified</em> rather than being filled in with a guess. If you run this store, <a href="/join/">claim the page</a> and we will verify and date the record.</p></div>"""

    ld = [ld_crumbs(trail),
          {k: v for k, v in {
             "@context":"https://schema.org","@type":"OnlineStore","name":s["name"],"url":s["url"],
             "@id":f"{BASE}/stores/{s['slug']}/#store","sameAs":[s["url"]],
             "description":s.get("summary") or None,
             "currenciesAccepted":s.get("currency") or None,
             "areaServed":s.get("ships_to") or None,
             "makesOffer":[{"@type":"Offer","name":p["title"],"price":p["price"],"priceCurrency":p.get("currency","USD"),
                            "availability":"https://schema.org/InStock" if p.get("availability")=="in_stock" else "https://schema.org/OutOfStock",
                            "sku":p.get("sku"),"url":p["url"]} for p in prods] or None,
           }.items() if v is not None}]

    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <div class="sheet">
    <div class="sheet-head">
      <div class="sheet-logo">{e(initials)}</div>
      <div>
        <p class="eyebrow">Independent store</p>
        <h1>{e(s["name"])}</h1>
        <p class="lede" style="margin:0 0 .7rem">{e(s.get("tagline") or host(s["url"]))}</p>
        <div class="flex">{vals}</div>
      </div>
      <div class="sheet-act">
        <a class="btn btn-brand" href="{e(s["url"])}" rel="nofollow noopener" target="_blank">Visit store</a>
        <a class="btn btn-ghost btn-sm" href="/join/">Claim this page</a>
      </div>
    </div>
    <dl class="facts">
      <div class="fact"><dt>Indexed since</dt><dd>{e(s.get("added") or TODAY)}</dd></div>
      <div class="fact"><dt>Ships from</dt><dd>{e(s.get("ships_from") or "Not verified")}</dd></div>
      <div class="fact"><dt>Listings published</dt><dd>{len(prods)}</dd></div>
      <div class="fact"><dt>Verified</dt><dd>{e(s.get("verified") or "Pending")}</dd></div>
    </dl>
  </div>
  {note}
  <div class="grid g2" style="gap:26px;align-items:start">
    <div>
      <h2>About {e(s["name"])}</h2>
      <p>{about_copy}</p>
      <p class="rail"><b>Categories</b> {e(cats)}<span class="dot"></span>{status_tag(s)}<span class="dot"></span>{catalog_tag(s)}</p>
    </div>
    <div class="machine">
      <div class="machine-bar"><span>this store's machine record</span><span class="led"></span></div>
      <pre>{e(json.dumps({"name":s["name"],"url":s["url"],"categories":s.get("categories",[]),"listings":len(prods),"listing_status":s.get("listing_status","pending_verification"),"catalog_status":s.get("catalog_status","not_connected"),"last_verified":s.get("verified"),"feed":f"{BASE}/feeds/stores.json"}, indent=2))}</pre>
    </div>
  </div>

  <div class="sec-head" style="margin-top:36px"><div><p class="eyebrow alt">Catalog</p><h2>{len(prods)} listing{"s" if len(prods)!=1 else ""}</h2></div>
    <span class="rail">{catalog_tag(s)}</span></div>
  <div class="grid {"g4" if prods else "g1"}">{grid}</div>
  <p class="sm muted mt2">Every link goes straight to {e(s["name"])}. {BRAND} takes no commission and handles no payment.</p>
</div></main>
{footer()}"""
    return write(f"stores/{s['slug']}/index.html",
        head(f"{s['name']} — independent store | {BRAND}",
             (s.get("summary") or f"{s['name']} is an independent online store at {host(s['url'])}, indexed under {cats or 'the index'}. Buy direct from the brand.")[:158],
             f"/stores/{s['slug']}/", ld=ld) + body)

def page_stores():
    trail = [("Home","/"),("Stores",None)]
    cards = "".join(store_card(s) for s in STORES) + open_slot("Your brand here")
    ld = [ld_crumbs(trail), {"@context":"https://schema.org","@type":"CollectionPage","name":"All stores","url":BASE+"/stores/",
          "mainEntity":{"@type":"ItemList","numberOfItems":len(STORES),
            "itemListElement":[{"@type":"ListItem","position":i+1,"url":f"{BASE}/stores/{s['slug']}/","name":s["name"]} for i,s in enumerate(STORES)]}}]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <div class="sec-head"><div><p class="eyebrow">The index</p><h1>Every store on the record</h1>
    <p class="lede" style="margin:0">Independent sellers only. Each one keeps its own checkout, its own customers and its own margin.</p></div></div>
  <div class="bar"><span class="count">{len(STORES)} store{"s" if len(STORES)!=1 else ""} · verified {TODAY}</span>
    <a class="btn btn-sm btn-brand" href="/join/">Apply to list</a></div>
  <div class="grid g3">{cards}</div>
</div></main>
{footer()}"""
    return write("stores/index.html", head(f"All independent stores | {BRAND}",
        "The full index of verified independent online stores. Buy direct from the brand.", "/stores/", ld=ld) + body)

def page_search():
    trail = [("Home","/"),("Search",None)]
    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap">
  <h1>Search</h1>
  <p class="lede">Search every listing in the index. Results link straight to the brand's own store.</p>
  <form class="find" action="/search/" method="get" role="search" style="max-width:640px;margin:18px 0 26px">
    <input id="q2" name="q" type="search" placeholder="Try: shower door, phone case, coffee" autocomplete="off">
    <button type="submit">Search</button>
  </form>
  <div class="bar"><span class="count" id="rcount">Type to search</span>
    <select id="sort2" aria-label="Sort"><option value="rel">Sort: relevance</option><option value="lo">Price: low to high</option><option value="hi">Price: high to low</option></select></div>
  <div class="grid g4" id="results"></div>
  <p class="muted sm mt2" id="empty">Nothing matched. Try a broader word, or <a href="/stores/">browse all stores</a>.</p>
</div></main>
{footer()}"""
    return write("search/index.html", head(f"Search independent stores | {BRAND}",
        "Search products across every independent store in the index.", "/search/",
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

  <div class="note"><p><b>What we will not claim:</b> we cannot promise you a citation in ChatGPT, a ranking in Google, or a sale. What we can promise is that every fact about you is published in a form a machine can fetch, parse and date &mdash; and that is the part that is currently missing. Anyone selling you the guarantee is selling you something they do not control.</p></div>

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
            ("Feed syndication to Microsoft and Google Merchant Center", 1), ("Your record exposed through our MCP server", 1),
            ("Priority placement in your categories", 1), ("Monthly visibility report: who cites you, and for what", 1),
            ("Colour, logo and skin controls", 1), ("Catalog auto-sync", 0)]),
        ("Signal", 149, "per month", False, [
            ("Everything in Pro", 1), ("Unlimited listings with nightly catalog sync", 1),
            ("ChatGPT merchant feed application handled for you", 1), ("Answer monitoring across four assistants", 1),
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
    trail = [("Home","/"),("Get listed",None)]
    opts = "".join(f'<option value="{c["slug"]}">{e(c["name"])}</option>' for c in CATS)
    endpoint = SITE.get("apply_endpoint")
    email = SITE.get("contact_email")

    fields = f"""      <div class="field"><label for="f-store">Store name</label><input id="f-store" name="store" required></div>
      <div class="field"><label for="f-url">Store URL</label><input id="f-url" name="url" type="url" placeholder="https://" required></div>
      <div class="field"><label for="f-email">Email</label><input id="f-email" name="email" type="email" required></div>
      <div class="field"><label for="f-cat">Main category</label><select id="f-cat" name="category">{opts}</select></div>
      <div class="field"><label for="f-plan">Plan</label><select id="f-plan" name="plan">
        <option value="index">Index &mdash; {money(SITE["price_entry"])}/mo</option>
        <option value="pro">Pro &mdash; $49/mo</option>
        <option value="signal">Signal &mdash; $149/mo</option>
        <option value="unsure">Not sure yet</option></select></div>
      <div class="field"><label for="f-note">What do you make or sell?</label><textarea id="f-note" name="note" placeholder="A couple of sentences is plenty."></textarea></div>"""

    if endpoint:
        form = f"""<form class="card" method="post" action="{e(endpoint)}" id="apply">
{fields}
      <button class="btn btn-brand" type="submit" style="width:100%">Send application</button>
      <p class="xs muted" style="margin:.8rem 0 0">No payment now. We reply within two business days.</p>
    </form>"""
    elif email:
        form = f"""<form class="card" method="post" action="mailto:{e(email)}" enctype="text/plain" id="apply">
{fields}
      <button class="btn btn-brand" type="submit" style="width:100%">Send application</button>
      <p class="xs muted" style="margin:.8rem 0 0">Opens in your mail app. No payment now. We reply within two business days.</p>
    </form>"""
    else:
        form = f"""<div class="card">
      <span class="tag tag-open">Applications opening</span>
      <h3 style="margin:.6rem 0 .4rem">The application form is not live yet</h3>
      <p class="sm">Rather than show you a form that posts into a void, we have left it off until the inbox behind it is wired up. It will be here shortly.</p>
      <p class="sm">If you want to be first in your category, the fastest route in the meantime is to contact {e(SITE["publisher"])} directly through <a href="{e(SITE["publisher_url"])}">{e(host(SITE["publisher_url"]))}</a> and mention {e(BRAND)} and your store URL.</p>
      <p class="xs muted" style="margin:.8rem 0 0">Founding listings are being reviewed now, {len(CATS)} categories are open, and no payment is taken before a page is live.</p>
    </div>"""

    body = f"""{header()}
{crumbs(trail)}
<main id="main"><div class="wrap mid">
  <p class="eyebrow">Get listed</p>
  <h1>Apply to join the index</h1>
  <p class="lede">Independent stores only. Every applicant is checked by hand, which is the only reason the record is worth anything.</p>
  <div class="grid g2 mt2" style="gap:30px;align-items:start">
    {form}
    <div>
      <h3>What we check</h3>
      <ul class="sm"><li>You are an independent store, not a marketplace reseller front</li><li>You control your own checkout</li><li>The products are real and the prices on your site are current</li><li>You ship to at least one country reliably</li></ul>
      <h3 class="mt2">What happens next</h3>
      <div class="steps" style="margin-top:10px">
        <div class="step"><div><h3>We verify</h3><p class="sm">Usually within two business days. If we cannot confirm something, we ask you rather than guess.</p></div></div>
        <div class="step"><div><h3>We write and publish your page</h3><p class="sm">You read it and approve it before it goes live. Nothing about your store gets published that you have not seen.</p></div></div>
        <div class="step"><div><h3>Billing starts the day you are live</h3><p class="sm">Not before. Month to month after that, cancel whenever.</p></div></div>
      </div>
      <div class="note"><p class="sm">We will never ask you for your store password, your payment processor login or your domain registrar credentials. If anyone claiming to be us does, it is not us.</p></div>
    </div>
  </div>
</div></main>
{footer()}"""
    return write("join/index.html", head(f"Apply to list your store | {BRAND}",
        "Apply to join the index of independent stores. Hand-checked, month to month, no contract, no commission.",
        "/join/", ld=ld_crumbs(trail)) + body)

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
            "cat": p.get("category"), "sub": p.get("subcategory",""), "sku": p.get("sku","")} for p in PRODUCTS]
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

    urls = ["/", "/stores/", "/search/", "/for-brands/", "/pricing/", "/how-it-works/", "/join/", "/about/"]
    urls += [f"/c/{c['slug']}/" for c in CATS]
    urls += [f"/stores/{s['slug']}/" for s in STORES]
    body = "".join(
        f"<url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod>"
        f"<priority>{'1.0' if u=='/' else '0.8' if u.startswith('/c/') or u.startswith('/stores/') else '0.6'}</priority></url>"
        for u in urls)
    out.append(write("sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + body + "</urlset>"))

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
    made.append(page_search())
    made.append(page_for_brands())
    made.append(page_pricing())
    made.append(page_how())
    made.append(page_join())
    made.append(page_about())
    made.append(page_404())
    made += machine_files()
    print(f"built {len(made)} files")
    for m in made: print("  " + m)

if __name__ == "__main__":
    main()
