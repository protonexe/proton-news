# 📺 PROTON NEWS // CRT TERMINAL v2.0

A high-fidelity, 1980s-style terminal dashboard for global news, finance, weather, sports, world events and live flight tracking.

## 🚀 Features (v2.0)

- **Dashboard**: the tile console at `/` — every tile opens a dedicated page (news, finance, sports, weather, world, planes, customize), shared header with live clocks, six phosphor palettes (Paper White default), state kept per browser.
- **News Reader** (`/news.html`): split-pane wire with unread tracking, sector chips, SAVED read-later, J/K keyboard walk, TTS, font sizing, copy link, and **full article-text extraction** from the publisher page (`/article/extract`). Bodies are labelled `FULL TEXT`, `PAYWALL PREVIEW` or fall back to the feed summary with a reason.
- **Deep links & history**: each open story gets `#a=<article>` in the URL; back/forward and reload restore the same story.
- **Read later + offline**: saving a story stores its extracted body in IndexedDB, so it reopens instantly and reads with no network (`?saved=1` filter, ★ markers).
- **Body search**: queries of 3+ characters also search extracted article bodies — locally from IndexedDB and server-side over the extraction cache (`/article/search`), with `BODY` hits marked in the wire.
- **Extraction cache**: memory + JSON disk cache (`cache/articles/`, 3-day TTL, auto-pruned), per-domain rate limiting with 429/503 retry, SSRF guard.
- **Finance Terminal**: Yahoo Finance OHLC + volume charts with hover tooltips, MA-20 overlay, volume bars, scroll-zoom / drag-pan (chartjs-plugin-zoom), range selector (1D→ALL), symbol search, market overview (indices/commodities/crypto/currencies/bonds) with sparklines.
- **Sports Scoreboard**: 17 ESPN leagues (NFL/NBA/MLB/NHL/WNBA/European soccer/UFC/...) with live badges, team logos, records, venue, broadcast, league filter, 60s auto-refresh.
- **World Map**: D3 Natural Earth map, countries with live sources highlighted, click → country news, search, USGS seismic alerts.
- **Planes Radar**: Leaflet map with live OpenSky flights, theme-aware tiles, heading-rotated altitude-coloured markers, click popups, locate-from-list, filters, 15-min auto-refresh.
- **Customize**: theme picker, feed manifest, reader state, saved-article counter, read-history reset.
- **Legacy app**: the original single-page console is preserved at `/legacy/`; UI experiments live under `/demos/`.
- **Retro Aesthetics**: CRT scanlines, monospace UI, ticker marquee, terminal prompts.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python) — `backend.py`
- **Frontend**: HTML5, CSS3, JavaScript — `frontend/` (`index.html`, page-per-tile + `dash.css`/`dash.js`/`dash-store.js`)
- **Visualization**: Chart.js 4 + zoom plugin (finance), D3.js (world), Leaflet (planes)
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
