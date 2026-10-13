# Commerce Plugs open feeds

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

Attribution: Commerce Plugs (https://commerceplugs.com).
