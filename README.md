# 📺 PROTON NEWS // CRT TERMINAL v1.0

A high-fidelity, 1980s-style terminal dashboard for global news aggregation and financial tracking.

## 🚀 Features

- **Global News Feed**: Parallel aggregation of ~36 verified global RSS sources.
- **Interactive Globe**: D3.js powered world map for country-based news filtering.
- **Financial Terminal**: Real-time stock, commodity, and crypto tracking via Yahoo Finance.
- **Retro Aesthetics**: CRT scanlines, green-on-black monospace UI, and terminal-style interaction.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualization**: Chart.js (Financials), D3.js & TopoJSON (World Map)
- **Data Sources**: Yahoo Finance API, Global RSS Feeds

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

## 📜 License

MIT
