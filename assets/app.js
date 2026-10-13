/* Commerce Plugs — progressive enhancement only.
   Every page is complete server-side HTML. This file adds search, sort and
   filtering for human visitors. Nothing here is required to read the site:
   crawlers and assistants that do not run JavaScript still get the full
   content, which is the entire point of how this index is built. */
(function () {
  "use strict";

  var INDEX_URL = (window.CP_INDEX || "/search-index.json");
  var cache = null;

  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function money(v) {
    var n = parseFloat(v);
    if (isNaN(n)) return "";
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function load() {
    if (cache) return Promise.resolve(cache);
    return fetch(INDEX_URL, { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { cache = d && d.items ? d.items : []; return cache; })
      .catch(function () { cache = null; return null; });
  }

  function card(it) {
    var img = it.img
      ? '<img src="' + esc(it.img) + '" alt="" loading="lazy" decoding="async">'
      : '<span class="sm muted">' + esc((it.sku || "").slice(0, 6)) + "</span>";
    var bits = [];
    if (it.b) bits.push("<b>" + esc(it.b) + "</b>");
    if (it.sub) bits.push(esc(it.sub));
    if (it.d) bits.push(esc(it.d));
    if (it.f) bits.push(esc(it.f));
    bits.push("in stock");
    if (it.sku) bits.push(esc(it.sku));
    return '<div class="row">' +
      '<span class="th">' + img + "</span>" +
      "<div>" +
        '<a class="ttl" href="' + esc(it.u) + '" rel="nofollow noopener" target="_blank">' + esc(it.t) + "</a>" +
        '<p class="meta">' + bits.join('<span class="sep">\u00b7</span>') + "</p>" +
      "</div>" +
      '<div class="amt"><span class="p">' + money(it.p) + "</span>" +
        '<a class="go" href="' + esc(it.u) + '" rel="nofollow noopener" target="_blank">' + esc(it.s) + " \u2192</a></div>" +
      "</div>";
  }

  function score(it, terms) {
    var hay = (it.t + " " + it.s + " " + (it.sub || "") + " " + (it.sku || "")).toLowerCase();
    var n = 0;
    for (var i = 0; i < terms.length; i++) {
      if (hay.indexOf(terms[i]) === -1) return 0;
      n += it.t.toLowerCase().indexOf(terms[i]) === 0 ? 3 : 1;
    }
    return n;
  }

  function sortItems(items, how) {
    var out = items.slice();
    if (how === "lo") out.sort(function (a, b) { return parseFloat(a.p) - parseFloat(b.p); });
    else if (how === "hi") out.sort(function (a, b) { return parseFloat(b.p) - parseFloat(a.p); });
    return out;
  }

  /* ---------------------------------------------------- /search/ */
  function initSearch() {
    var box = $("#results");
    var count = $("#rcount");
    var empty = $("#empty");
    if (!box || !count) return false;

    var q = new URLSearchParams(location.search).get("q") || "";
    var cat = new URLSearchParams(location.search).get("c") || "";
    var input = $("#q2") || $("#q");
    if (input && q) input.value = q;
    if (empty) empty.hidden = true;

    function render() {
      load().then(function (items) {
        if (items === null) {
          count.textContent = "Search is unavailable right now.";
          box.innerHTML = '<div class="slot"><h3>Could not load the index</h3>' +
            "<p>The search index did not load. Every page on this site is readable without it — " +
            '<a href="/stores/">browse all stores</a> instead.</p></div>';
          return;
        }
        if (!items.length) {
          count.textContent = "0 listings published";
          box.innerHTML = '<div class="slot"><span class="tag">Index opening</span>' +
            "<h3>No product listings are published yet</h3>" +
            "<p>Listings appear here when a store connects a catalog feed. We do not generate " +
            "placeholder products to make the index look fuller than it is. " +
            '<a href="/stores/">See the stores on the index</a>, or ' +
            '<a href="/for-brands/">list your brand</a>.</p></div>';
          if (empty) empty.hidden = true;
          return;
        }
        var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
        var hits = items;
        if (cat) hits = hits.filter(function (it) { return it.cat === cat; });
        if (terms.length) {
          hits = hits.map(function (it) { return { it: it, sc: score(it, terms) }; })
                     .filter(function (x) { return x.sc > 0; })
                     .sort(function (a, b) { return b.sc - a.sc; })
                     .map(function (x) { return x.it; });
        }
        var how = $("#sort2") ? $("#sort2").value : "rel";
        hits = sortItems(hits, how);

        if (!q && !cat) {
          count.textContent = items.length + " listing" + (items.length === 1 ? "" : "s") + " in the index";
        } else {
          count.textContent = hits.length + " result" + (hits.length === 1 ? "" : "s") +
            (q ? ' for "' + q + '"' : "");
        }
        box.innerHTML = hits.map(card).join("");
        if (empty) empty.hidden = hits.length > 0;
      });
    }

    var sel = $("#sort2");
    if (sel) sel.addEventListener("change", render);
    render();
    return true;
  }

  /* ------------------------------------------- category sort + filter */
  function initCategory() {
    var box = $("#results");
    var sel = $("#sort");
    if (!box) return;
    var cards = $$(".row", box);
    if (!cards.length) return;

    function priceOf(el) {
      var t = $(".price", el);
      return t ? parseFloat(t.textContent.replace(/[^0-9.]/g, "")) : 0;
    }
    function subOf(el) {
      var r = $(".meta", el);
      if (!r) return "";
      var parts = r.textContent.split("·");
      return (parts[parts.length - 1] || "").trim();
    }

    if (sel) {
      sel.addEventListener("change", function () {
        var vis = cards.slice().sort(function (a, b) {
          if (sel.value === "lo") return priceOf(a) - priceOf(b);
          if (sel.value === "hi") return priceOf(b) - priceOf(a);
          return cards.indexOf(a) - cards.indexOf(b);
        });
        vis.forEach(function (c) { box.appendChild(c); });
      });
    }

    var boxes = $$("[data-sub]");
    if (boxes.length) {
      boxes.forEach(function (cb) {
        cb.addEventListener("change", function () {
          var on = boxes.filter(function (b) { return b.checked; })
                        .map(function (b) { return b.getAttribute("data-sub"); });
          cards.forEach(function (c) {
            c.hidden = on.length > 0 && on.indexOf(subOf(c)) === -1;
          });
          var n = cards.filter(function (c) { return !c.hidden; }).length;
          var ct = $(".count");
          if (ct) ct.setAttribute("data-filtered", n);
        });
      });
    }
  }

  function init() {
    if (!initSearch()) initCategory();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
