# commerceplugs.com

An index of independent online stores. Shoppers search it and click through to the
brand's own site. Machines read the same pages as a source. We take no commission
and host no checkout.

Published by Eye To Ad Media.

## How this site is built

A single Python script with no dependencies reads `data/*.json` and writes the
entire site as static HTML. There is no framework, no build toolchain and no
client-side rendering of content.

```
python3 build.py
```

That writes `index.html`, every category and store page, the open feeds, the MCP
server definition, `robots.txt`, `llms.txt` and `sitemap.xml`. Commit the output —
GitHub Pages serves it directly from the branch root.

### Why static and server-rendered

The crawlers behind the major AI assistants do not execute JavaScript. Anything
rendered client-side is invisible to them. Every page here is complete in the
first HTTP response, which is the entire premise of the product.

`assets/app.js` adds search, sorting and filtering for human visitors only. No
content depends on it.

## Data

| File | What it holds |
|---|---|
| `data/site.json` | Brand, domain, entry price, publisher, contact endpoints. |
| `data/categories.json` | The 16 categories, their blurbs and icon keys. |
| `data/stores.json` | One record per listed store. |
| `data/products.json` | Listings, only from stores with a connected catalog feed. |

### Data policy — read this before adding anything

**Nothing in `data/` may be estimated, inferred or filled in to look complete.**

A field we have not confirmed with the store is `null`. The generator renders
`null` as "Not verified" and says so plainly on the page. A store with no
connected catalog contributes zero products and its page says that too.

This is not pedantry. The product being sold is a record a machine can trust,
and the fastest way to make that record worthless is to pad it. If the index
looks small, it is small.

- `listing_status`: `pending_verification` until a human confirms the store.
- `catalog_status`: `not_connected` until a real catalog feed is wired up.
- `verified`: `null` until verified, then an ISO date.

## Configuration

`data/site.json` carries two optional endpoints:

- `apply_endpoint` — a form POST URL (e.g. a Formspree form). When set, `/join/`
  renders a live application form.
- `contact_email` — used as a `mailto:` fallback when `apply_endpoint` is unset.

When both are `null`, `/join/` renders an honest "not live yet" panel rather than
a form that posts into a void. Set one before launch.

## Machine-facing surface

| Path | What it is |
|---|---|
| `/feeds/stores.json` | Every store, with status and verification date. |
| `/feeds/products.json` | Every listing. |
| `/feeds/products.tsv` | The same catalog in the agentic-commerce product feed column shape. |
| `/.well-known/mcp/server.json` | Tool definitions so an assistant can query the index directly. |
| `/llms.txt` | Plain-text orientation for retrieval. |
| `/robots.txt` | Permissive to every major AI crawler, deliberately. |

## Deployment

GitHub Pages from this branch root. `CNAME` points at `commerceplugs.com` and
`.nojekyll` stops Jekyll from eating the `.well-known` directory.
