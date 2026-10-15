# 📺 PROTON NEWS // CRT TERMINAL v2.0

A high-fidelity, 1980s-style terminal dashboard for global news, finance, weather, sports, world events and live flight tracking.

## 🚀 Features (v2.0)

- **Global News Feed**: 122 RSS sources across 60 countries, 3 stories each, deduped, sector-tagged (TECH/FINANCE/ENERGY/HEALTH/POLITICS/SPORTS/CLIMATE).
- **Finance Terminal**: Yahoo Finance OHLC + volume charts with hover tooltips, MA-20 overlay, volume bars, scroll-zoom / drag-pan (chartjs-plugin-zoom), range selector (1D→ALL), symbol search, market overview (indices/commodities/crypto/currencies/bonds) with sparklines.
- **Sports Scoreboard**: 17 ESPN leagues (NFL/NBA/MLB/NHL/WNBA/European soccer/UFC/...) with live badges, team logos, records, venue, broadcast, league filter, 60s auto-refresh.
- **World Map**: D3 Natural Earth map, countries with live sources highlighted, click → country news, search, USGS seismic alerts.
- **Planes Radar**: Leaflet dark map with 300 live OpenSky flights, heading-rotated markers, click popups (callsign/country/alt/speed/heading/ICAO), locate-from-list, 30s auto-refresh, callsign filter.
- **Customize**: add/remove your own RSS feeds (persisted), toggle news categories on/off, browse all built-in sources, export news as JSON.
- **Retro Aesthetics**: CRT scanlines, green-on-black monospace UI, ticker marquee, CLI (`goto`, `search`, `addfeed`, `refresh`, `help`).

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python) — `backend.py`
- **Frontend**: HTML5, CSS3, JavaScript — `frontend/index.html` (+ `globe-data.js`)
- **Visualization**: Chart.js 4 + zoom plugin (finance), D3.js (world), Leaflet (planes)
- **Data**: Yahoo Finance, ESPN scoreboard API, OpenSky Network, Open-Meteo, USGS, 122 global RSS feeds

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
