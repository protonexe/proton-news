# RETRO-NEWS // HANDOFF / TODO

> Continue-from-here document. The News section is **done and running**.
> The Stocks and Globe sections are **researched but NOT yet implemented**.

---

## 1. Project location

```
C:\Users\rejip\retro-news\
├── backend.py                    (FastAPI — news + static + stocks[pending])
├── requirements.txt              (fastapi, uvicorn, feedparser)
├── frontend\
│   └── index.html                (CRT terminal UI — news done, stocks/globe pending)
├── .venv\                        (Python 3.14 venv, uvicorn installed here)
└── HANDOFF.md                    (this file)
```

**Currently running:** `uvicorn backend:app` on `http://localhost:6767/` (single process, serves both the site and the API).

---

## 2. What is DONE ✅

### News section (live at http://localhost:6767/)
- 52 RSS sources, grouped into 6 categories, fetched in parallel (`ThreadPoolExecutor`, 40 workers, 10s socket timeout).
- **35 real headlines working**, 17 returning "[ Feed returned no entries ]" (URL guesses were wrong — fix list in §6).
- Frontend: pure HTML/CSS/JS, retro CRT (Terminal.css CDN + custom green-on-black `#050505`/`#33ff33` + scanline `repeating-linear-gradient`).
- Top headline per source, rendered as `<fieldset>` blocks with category as `<legend>`.
- The site is served by FastAPI itself (`StaticFiles` mount at `/`), so the browser uses the same origin for `/news` — no CORS, no `file://`.

### Files
- `backend.py` — FastAPI app, CORS, 52-source aggregator, serves `frontend/` at `/`. Port **6767**.
- `frontend/index.html` — 129 lines. News section fully working.

---

## 3. What is PENDING ❌ (the user's last request)

The user asked for **two new sections** + a **top-bar nav** to switch between them:

1. **STOCKS section** — "stock performance with graphs and all data available, look online for resources"
2. **GLOBE / MAP section** — "interactive globe/map, click a country → news from that country in the sidebar"
3. **Top-bar nav** — 3 buttons (`[ NEWS ] [ STOCKS ] [ GLOBE ]`) that show/hide the corresponding section.

**Nothing of this is implemented yet** — only the research below is done.

---

## 4. Research findings (resources to use) 🔍

### 4a. Stock data — **Yahoo Finance v8 chart API** (no API key)

Confirmed by web search (dev.to, 2026): the v8 chart endpoint is the best free, no-key source for historical OHLCV in 2026.

```
GET https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1y&interval=1d
```

- **MUST** send a browser `User-Agent` header (rejects default `python-requests/2.x`).
- No API key, no signup. Free, covers decades of history, multiple intervals.
- Rate limit: stay under ~2 req/sec.
- Response shape: `chart.result[0].meta` (regularMarketPrice, previousClose, currency, …) + `chart.result[0].indicators.quote[0]` (open/high/low/close/volume arrays) + `chart.result[0].timestamp` (unix seconds).
- That gives you everything for "all data available": last close, prev close, change, change%, day OHL, volume, 52-week high/low (from the 1y series), plus the full 1y series for the chart.

> Other options considered: Stooq (CSV, no key, but less reliable / format quirks), Alpha Vantage (25 req/day free, needs key), Finnhub (needs key). Yahoo v8 is the winner for zero-friction.

**Recommended backend endpoint:**
```
GET /stocks/<symbol>   →   {
  symbol, name, currency,
  last, previousClose, change, changePct,
  dayOpen, dayHigh, dayLow, volume,
  fiftyTwoHigh, fiftyTwoLow,
  history: [ {date, close}, ... ]   // last 252 trading days
}
```
A small frontend ticker list (AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, ^GSPC, ^DJI, ^IXIC) with buttons to switch.

### 4b. Stock chart — **Chart.js** (CDN)

```
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

Line chart of closes, styled retro (green line `#33ff33` on dark grid) to match the CRT theme. Lightweight, no build step.

### 4c. Interactive world map — **d3-geo + world-atlas TopoJSON** (CDN)

Confirmed standard. Three CDN deps:
```
https://cdn.jsdelivr.net/npm/d3@7
https://cdn.jsdelivr.net/npm/topojson-client@3
https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json   (the data)
```

- `d3.geoNaturalEarth1()` projection (or `geoMercator`) → `d3.geoPath` → SVG `<path>` per country.
- Each feature has `properties.name` (country name, e.g. `"Germany"`) and `id` (ISO 3166-1 numeric).
- **2D SVG map** (recommended): retro, lightweight, on-theme (green countries on black). 
  - Alternative 3D: `globe.gl` (heavier, WebGL, less retro). User didn't specify, but 2D fits the CRT aesthetic.
- Click handler: `path.on("click", (e,d) => filterNewsByCountry(d.properties.name))`.
- Highlight countries that have feeds (data-driven fill based on the country set derived from the news).

---

## 5. Implementation plan for the pending work

### Backend (`backend.py`)

1. **Add `country` to every entry in `RAW_FEEDS`** (each feed → an ISO-ish country name string, e.g. `"United States"`, `"United Kingdom"`, `"Germany"`). The `_fetch_one` function must include `"country": feed["country"]` in every story dict (both real entries and the error/empty fallback dicts), so the frontend can filter by it.

2. **Add `/stocks/<symbol>` endpoint** that:
   - Validates the symbol (allowlist of ~10 tickers is simplest, or just pass through).
   - Fetches `https://query1.finance.yahoo.com/v8/finance/chart/<SYMBOL>?range=1y&interval=1d` with a browser `User-Agent`.
   - Parses the JSON, derives `last`/`previousClose`/`change`/`changePct`/`dayOHL`/`volume`/`fiftyTwoHigh`/`fiftyTwoLow` from `meta` + the last 1y series, and returns the dict shown in §4a.
   - Uses `urllib.request` (no new pip dep; `requests` is *not* installed).

### Frontend (`frontend/index.html`)

1. **Add a sticky top nav bar** with three retro buttons:
   ```html
   <nav id="topnav">
     <button data-section="news"   class="active">[ NEWS   ]</button>
     <button data-section="stocks">[ STOCKS ]</button>
     <button data-section="globe">[ GLOBE  ]</button>
   </nav>
   ```
   Vanilla-JS section switching: `.section { display:none }` / `.section.active { display:block }`.

2. **Wrap the existing news content in `<section id="sec-news" class="section active">`** (no functional change — just a wrapper + the show/hide logic).

3. **Add `<section id="sec-stocks" class="section">`** with:
   - A row of ticker buttons (the allowlist).
   - A `<canvas id="stock-chart">` for Chart.js.
   - A stats grid (last, change, change%, OHL, volume, 52w H/L).
   - A `loadStock(symbol)` function that fetches `/stocks/<symbol>` and updates the chart + stats.

4. **Add `<section id="sec-globe" class="section">`** with a two-pane layout:
   - **Left/main:** `<svg id="worldmap">` (filled by d3).
   - **Right sidebar:** a scrollable div `#country-news` that shows fieldsets for the clicked country.
   - A `loadMap()` function: fetches the world-atlas topojson, renders the SVG, and attaches click handlers. On click, filter the already-loaded `allStories` array by `story.country === clickedName` and render into `#country-news`. If the country has no stories, show "No sources from this country."
   - `loadMap()` should be called once on first switch to the globe section (lazy), and it depends on `allStories` being loaded (so call `loadNews()` first, or share state).

5. **Add the three CDN `<script>` tags** in `<head>` (Chart.js, d3, topojson-client). The world-atlas JSON is fetched at runtime, not as a `<script>`.

6. Keep the CRT theme: `#33ff33` on `#050505`, monospace, the scanline `::before`, the fieldset/legend styling. The map fills (countries) `#0a3a0a` by default, `#33ff33` for countries that have feeds, and a brighter `#aaffaa` on hover/click. Sidebar matches the news layout.

### Country → country-name mapping (for tagging the 52 feeds)

Use the exact string `world-atlas` uses in `properties.name` (e.g. `"United States of America"` for USA? — verify against the topojson; Natural Earth names like `"United States of America"`). The join key is the country NAME string. Plan:
- Reuters → `United Kingdom` (HQ London)
- AP → `United States of America`
- AFP → `France`
- CNN/NPR/Fox/CBS/NBC/ABC/CNBC/PBS → `United States of America`
- NYT/WaPo/WSJ/USA Today/LA Times/NY Post/Politico/Time → `United States of America`
- BBC/Guardian/FT/Independent/Telegraph/Sky News → `United Kingdom`
- DW → `Germany`; Spiegel → `Germany`; France24 → `France`; Euronews → `France`; El País → `Spain`
- CBC/Globe&Mail → `Canada`
- ABC(AU)/SMH → `Australia`; NZ Herald → `New Zealand`
- Al Jazeera → `Qatar`; Arab News → `Saudi Arabia`; Times of Israel → `Israel`
- SCMP → `Hong Kong`; CNA → `Singapore`; Nikkei → `Japan`
- India Times / The Hindu → `India`
- AllAfrica → `South Africa` (or skip — pan-regional); M&G → `South Africa`
- Bloomberg/Forbes/TechCrunch/Verge/Wired/Ars → `United States of America`; The Economist → `United Kingdom`

> **Important:** verify the exact `properties.name` strings by loading `world-atlas/countries-110m.json` and checking the names array, then make the feed `country` values match exactly (the frontend join is a string equality on `properties.name`).

---

## 6. Known issues / things to fix

### Broken feed URLs (17) — replace the URL in `RAW_FEEDS`
```
feeds.reuters.com/reuters/topNews
feeds.apnews.com/rss/apf-topnews
www.afp.com/en/rss/afp-english-news
www.pbs.org/newshour/feed
www.usatoday.com/rss/news/
www.latimes.com/world/rss
www.politico.com/rss/politicopicks.xml
english.elpais.com/feed/
www.cbc.ca/webfeed/rss/rss-top-stories
www.theglobeandmail.com/feed/
www.nzherald.co.nz/rss/
www.scmp.com/feed/
www.indiatimes.com/rss/
asia.nikkei.com/rss/feed
www.arabnews.com/rss.xml
allafrica.com/tools/headlines/rss/english.xml
www.economist.com/world-week/rss.xml
```
Find the correct RSS path for each and swap them in.

### Performance
- First `/news` call takes ~20–25s (52 parallel feeds, 10s socket timeout, cold DNS). The frontend shows "loading..." for that long on first open. Subsequent calls are faster (warm caches). 
- **Suggested fix (not implemented):** add a simple in-memory cache in `get_news()` (e.g. 120s TTL) — the frontend refresh would then be instant.

### Windows / uvicorn gotchas (already learned)
- `uvicorn --reload` (StatReload) **hangs on Windows** after a file change (it gets stuck in "Reloading..." and the new server never starts). **Do NOT use `--reload` on Windows.** Edit `backend.py`, then manually restart:
  ```bat
  taskkill /F /PID <old_pid>
  .venv\Scripts\uvicorn.exe backend:app --host localhost --port 6767
  ```
  (the launch command is in §7).
- The venv's `python` on this machine defaults to `cp1252` for file I/O, which **breaks UTF-8 JSON** (e.g. international summaries). Fix when parsing in scripts: `PYTHONUTF8=1 python -c '...'` or `open(..., encoding="utf-8")`.

### LSP "errors" (harmless false positives)
Lines in `backend.py` that touch `entry.get("title")` / `entry.get("summary")` show pyright LSP errors because feedparser's stubs type those as `str | list[FeedParserDict] | ...`. At runtime feedparser returns a string for these fields, so `.strip()` and `_clean_summary(...)` work fine. Safe to ignore.

---

## 7. Commands to run

```bat
:: activate venv
cd C:\Users\rejip\retro-news
.venv\Scripts\activate

:: install deps (already done)
pip install -r requirements.txt

:: run the site (NO --reload on Windows — it hangs)
.venv\Scripts\uvicorn.exe backend:app --host localhost --port 6767

:: open in browser
::   http://localhost:6767/

:: stop the server
taskkill /F /IM uvicorn.exe   :: or note the PID from the log
```

---

## 8. Resume checklist (for the next session)

When continuing, in order:

- [ ] Read this `HANDOFF.md` and skim `backend.py` + `frontend/index.html`.
- [ ] Load `world-atlas/countries-110m.json` once and dump the `properties.name` values to confirm the exact country-name strings (the join key).
- [ ] Backend: add `country` to each of the 52 `RAW_FEEDS` entries; make `_fetch_one` include `country` in every story dict (including the error/empty fallback so the sidebar can show "[no stories]").
- [ ] Backend: add `/stocks/<symbol>` (Yahoo v8, browser User-Agent, urllib). Add a tiny `_YAHOO_UA` constant.
- [ ] Frontend: add the top-bar `<nav>` and the 3 `<section>` wrappers + show/hide JS.
- [ ] Frontend: add Chart.js + build the STOCKS section (ticker row, canvas, stats grid, `loadStock`).
- [ ] Frontend: add d3 + topojson-client CDN; build the GLOBE section (SVG map, click → filter `allStories` by `country` → render into `#country-news`).
- [ ] Restart uvicorn (no `--reload`): `taskkill /F /PID <pid>` then relaunch.
- [ ] Verify: `curl http://localhost:6767/stocks/AAPL` and `curl http://localhost:6767/` in the browser.
- [ ] (Optional) Fix the 17 broken feed URLs in `RAW_FEEDS`.
- [ ] (Optional) Add a 120s response cache in `get_news()` for snappier frontend reloads.
