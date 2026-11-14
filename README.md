# 📺 PROTON NEWS // CRT TERMINAL v2.0

A high-fidelity, 1980s-style terminal dashboard for global news, finance, weather, sports, world events and live flight tracking.

## 🚀 Features (v2.0)

- **Dashboard**: the tile console at `/` — every tile opens a dedicated page (news, finance, sports, weather, world, planes, customize), shared header with live clocks, six phosphor palettes (Paper White default), state kept per browser.
- **News Reader** (`/news.html`): split-pane wire with unread tracking, sector and region filters, SAVED read-later, J/K keyboard walk, TTS, font sizing, copy link, and **full article-text extraction** from the publisher page (`/article/extract`). Reader controls are grouped into compact PREV/POS/NEXT, SAVE/READ/COPY and TEXT segments. Bodies are labelled `FULL TEXT`, `PAYWALL PREVIEW` or fall back to the feed summary with a reason.
- **Deep links & history**: each open story gets `#a=<article>` in the URL; back/forward and reload restore the same story.
- **Read later + offline**: saving a story stores its extracted body in IndexedDB, so it reopens instantly and reads with no network (`?saved=1` filter, ★ markers).
- **Body search**: queries of 3+ characters also search extracted article bodies — locally from IndexedDB and server-side over the extraction cache (`/article/search`), with `BODY` hits marked in the wire.
- **Extraction cache**: memory + JSON disk cache (`cache/articles/`, 3-day TTL, auto-pruned), per-domain rate limiting with 429/503 retry, SSRF guard.
- **Finance Terminal**: SVG range chart with an animated line draw and filled area, range selector (1D→1Y), symbol search, quote statistics, and a `CHART`/`CRYPTO` sub-section split so the top-12 crypto board lives inside finance (click a coin to chart its symbol).
- **Sports Terminal**: 16 ESPN leagues (NFL/NBA/MLB/NHL/WNBA/European soccer/UFC/...) with live badges, team logos, records, venue, broadcast and league filter, plus a `SCOREBOARD`/`STANDINGS` tab split. Standings load lazily, split conferences/leagues side-by-side and use league-specific columns (W/L/PCT/GB, W/L/OTL/PTS, W/D/L/PTS/GD).
- **Weather Station** (`/weather.html`): Open-Meteo current conditions (feels-like, humidity, dew point, pressure, cloud, visibility, precipitation, gusts), a 24-hour hourly strip, 7-day forecast, sun/daylight panel and air-quality board (US/EU AQI, PM2.5, PM10, NO₂, SO₂, CO, O₃).
- **World Coverage**: an interactive 3D globe (globe.gl + TopoJSON) colour-coded by story volume - hover for counts, click to select and filter a country, double-click to open the reader. If WebGL is unavailable the same data renders as an interactive 2D SVG world map, so the page always works. Country/region distribution is computed from the live `/news/quick` wire, with share bars, search, top-country stats and click-through links (`news.html?country=` / `?region=`).
- **Planes Radar**: spinning 3D globe (globe.gl/three-globe) with live OpenSky flights rendered as small heading-aligned aircraft models (instanced meshes, altitude-tinted), drag-to-spin and scroll-zoom, hover tooltips, click/hover raycast selection, `SPIN` toggle and a theme-tinted globe atmosphere. A theme-aware Leaflet map remains as a toggle/fallback.
- **Customize**: theme picker, feed manifest, reader state, saved-article counter, read-history reset.
- **Legacy app**: the original single-page console is preserved at `/legacy/`; UI experiments live under `/demos/`.
- **Retro Aesthetics**: CRT scanlines, monospace UI, ticker marquee, terminal prompts.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python) — `backend.py`
- **Frontend**: HTML5, CSS3, JavaScript — `frontend/` (`index.html`, page-per-tile + `dash.css`/`dash.js`/`dash-store.js`)
- **Visualization**: hand-rolled animated SVG range charts (finance), globe.gl + Three.js + Leaflet (planes), globe.gl + TopoJSON (world)
- **Data**: Yahoo Finance, ESPN scoreboard API, OpenSky Network, Open-Meteo, USGS, 122 global RSS feeds, trafilatura article extraction

## 💻 Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/protonexe/proton-news.git
cd proton-news
```

### 2. Create a virtual environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the terminal
```bash
python backend.py
```
The terminal will be available at `http://127.0.0.1:6767`

## AI Disclosure

AI was used in the making of this project to assist with development.



## 📜 License

MIT
