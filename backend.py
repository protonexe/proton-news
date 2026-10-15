import json
import os
import re
import socket
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from urllib.parse import urlparse

import feedparser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

socket.setdefaulttimeout(12)

# Some feeds block non-browser user agents. Fetch bytes ourselves with a
# browser UA, then hand bytes to feedparser.
feedparser.USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

app = FastAPI(title="Proton News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Country values MUST match frontend globe ADMIN names (Natural Earth).
# See frontend/globe-data.js window.__GEO__ properties.ADMIN.
RAW_FEEDS = [
    # ---- NORTH AMERICA ----
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "http://rss.cnn.com/rss/cnn_topstories.rss"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "http://rss.cnn.com/rss/edition_world.rss"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://feeds.npr.org/1001/rss.xml"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://moxie.foxnews.com/google-publisher/latest.xml"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://www.cbsnews.com/latest/rss/main"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://feeds.nbcnews.com/nbcnews/public/news"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://feeds.abcnews.com/abcnews/topstories"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://feeds.washingtonpost.com/rss/homepage"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://nypost.com/feed/"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://time.com/feed/"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://news.google.com/rss"},
    {"category": "NORTH AMERICA", "country": "Canada", "url": "https://www.cbc.ca/cmlink/rss-topstories"},
    {"category": "NORTH AMERICA", "country": "Canada", "url": "https://globalnews.ca/feed/"},
    {"category": "NORTH AMERICA", "country": "Canada", "url": "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822289"},
    {"category": "NORTH AMERICA", "country": "Mexico", "url": "https://mexiconewsdaily.com/feed/"},
    # ---- LATIN AMERICA ----
    {"category": "LATIN AMERICA", "country": "Brazil", "url": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml"},
    {"category": "LATIN AMERICA", "country": "Brazil", "url": "https://riotimesonline.com/feed/"},
    {"category": "LATIN AMERICA", "country": "Argentina", "url": "https://www.batimes.com.ar/feed/"},
    {"category": "LATIN AMERICA", "country": "Colombia", "url": "https://colombiareports.com/feed/"},
    {"category": "LATIN AMERICA", "country": "Peru", "url": "https://andina.pe/ingles/rss.xml"},
    {"category": "LATIN AMERICA", "country": "Chile", "url": "https://www.biobiochile.cl/lista/rss.xml"},
    # ---- UK & IRELAND ----
    {"category": "UK & IRELAND", "country": "United Kingdom", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"category": "UK & IRELAND", "country": "United Kingdom", "url": "https://www.theguardian.com/world/rss"},
    {"category": "UK & IRELAND", "country": "United Kingdom", "url": "https://feeds.skynews.com/feeds/rss/world.xml"},
    {"category": "UK & IRELAND", "country": "United Kingdom", "url": "https://www.independent.co.uk/news/world/rss"},
    {"category": "UK & IRELAND", "country": "United Kingdom", "url": "https://www.telegraph.co.uk/rss.xml"},
    {"category": "UK & IRELAND", "country": "United Kingdom", "url": "https://www.economist.com/finance-and-economics/rss.xml"},
    {"category": "UK & IRELAND", "country": "United Kingdom", "url": "https://www.economist.com/science-and-technology/rss.xml"},
    {"category": "UK & IRELAND", "country": "Ireland", "url": "https://www.rte.ie/rss/news.xml"},
    {"category": "UK & IRELAND", "country": "Ireland", "url": "https://www.irishtimes.com/cmlink/news-1.1319192"},
    # ---- WESTERN EUROPE ----
    {"category": "WESTERN EUROPE", "country": "Germany", "url": "https://rss.dw.com/xml/rss-en-world"},
    {"category": "WESTERN EUROPE", "country": "Germany", "url": "https://www.spiegel.de/international/index.rss"},
    {"category": "WESTERN EUROPE", "country": "Germany", "url": "http://www.tagesschau.de/xml/rss2"},
    {"category": "WESTERN EUROPE", "country": "France", "url": "https://www.france24.com/en/rss"},
    {"category": "WESTERN EUROPE", "country": "France", "url": "https://www.euronews.com/rss"},
    {"category": "WESTERN EUROPE", "country": "France", "url": "https://www.lemonde.fr/rss/une.xml"},
    {"category": "WESTERN EUROPE", "country": "Spain", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
    {"category": "WESTERN EUROPE", "country": "Spain", "url": "https://english.elpais.com/rss/"},
    {"category": "WESTERN EUROPE", "country": "Italy", "url": "https://www.ansa.it/english/rss/ansa_english_topnews.xml"},
    {"category": "WESTERN EUROPE", "country": "Netherlands", "url": "https://www.dutchnews.nl/feed/"},
    {"category": "WESTERN EUROPE", "country": "Netherlands", "url": "https://nltimes.nl/feed"},
    {"category": "WESTERN EUROPE", "country": "Belgium", "url": "https://www.brusselstimes.com/feed"},
    {"category": "WESTERN EUROPE", "country": "Switzerland", "url": "https://www.swissinfo.ch/eng/rss"},
    {"category": "WESTERN EUROPE", "country": "Portugal", "url": "https://www.theportugalnews.com/rss.xml"},
    {"category": "WESTERN EUROPE", "country": "Greece", "url": "https://www.ekathimerini.com/rss/news/"},
    # ---- NORTHERN EUROPE ----
    {"category": "NORTHERN EUROPE", "country": "Sweden", "url": "https://www.thelocal.se/feed"},
    {"category": "NORTHERN EUROPE", "country": "Norway", "url": "https://www.thelocal.no/feed"},
    {"category": "NORTHERN EUROPE", "country": "Denmark", "url": "https://www.thelocal.dk/feed"},
    {"category": "NORTHERN EUROPE", "country": "Finland", "url": "https://www.helsinkitimes.fi/rss.xml"},
    {"category": "NORTHERN EUROPE", "country": "Iceland", "url": "https://icelandreview.com/feed/"},
    {"category": "NORTHERN EUROPE", "country": "Poland", "url": "https://notesfrompoland.com/feed/"},
    {"category": "NORTHERN EUROPE", "country": "Poland", "url": "https://tvpworld.com/feed"},
    # ---- CENTRAL / EASTERN EUROPE ----
    {"category": "EASTERN EUROPE", "country": "Czechia", "url": "https://english.radio.cz/rss"},
    {"category": "EASTERN EUROPE", "country": "Hungary", "url": "https://dailynewshungary.com/feed/"},
    {"category": "EASTERN EUROPE", "country": "Romania", "url": "https://www.romania-insider.com/rss.xml"},
    {"category": "EASTERN EUROPE", "country": "Ukraine", "url": "https://kyivindependent.com/feed/"},
    {"category": "EASTERN EUROPE", "country": "Ukraine", "url": "https://www.kyivpost.com/feed"},
    {"category": "EASTERN EUROPE", "country": "Russia", "url": "https://www.themoscowtimes.com/rss/news"},
    {"category": "EASTERN EUROPE", "country": "Russia", "url": "https://tass.com/rss/v2.xml"},
    {"category": "EASTERN EUROPE", "country": "Turkey", "url": "https://www.hurriyetdailynews.com/rss/home"},
    {"category": "EASTERN EUROPE", "country": "Turkey", "url": "https://www.dailysabah.com/rss/turkey"},
    # ---- MIDDLE EAST ----
    {"category": "MIDDLE EAST", "country": "Qatar", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"category": "MIDDLE EAST", "country": "Qatar", "url": "https://www.gulf-times.com/rss"},
    {"category": "MIDDLE EAST", "country": "Saudi Arabia", "url": "https://www.arabnews.com/rss.xml"},
    {"category": "MIDDLE EAST", "country": "United Arab Emirates", "url": "https://gulfnews.com/rss-feed/uae"},
    {"category": "MIDDLE EAST", "country": "United Arab Emirates", "url": "https://www.khaleejtimes.com/rss/uae"},
    {"category": "MIDDLE EAST", "country": "Israel", "url": "https://www.timesofisrael.com/feed/"},
    {"category": "MIDDLE EAST", "country": "Israel", "url": "https://www.jpost.com/rss/rssfeedsfrontpage.aspx"},
    {"category": "MIDDLE EAST", "country": "Egypt", "url": "https://english.ahram.org.eg/RSSWorld.aspx"},
    {"category": "MIDDLE EAST", "country": "Iran", "url": "https://www.tehrantimes.com/rss"},
    {"category": "MIDDLE EAST", "country": "Lebanon", "url": "https://www.dailystar.com.lb/rss/News/Lebanon.ashx"},
    # ---- AFRICA ----
    {"category": "AFRICA", "country": "South Africa", "url": "https://mg.co.za/feed/"},
    {"category": "AFRICA", "country": "South Africa", "url": "https://feeds.news24.com/articles/news24/TopStories/rss"},
    {"category": "AFRICA", "country": "Nigeria", "url": "https://www.vanguardngr.com/feed/"},
    {"category": "AFRICA", "country": "Nigeria", "url": "https://punchng.com/feed/"},
    {"category": "AFRICA", "country": "Kenya", "url": "https://nation.africa/kenya/rss"},
    {"category": "AFRICA", "country": "Ghana", "url": "https://www.myjoyonline.com/feed/"},
    {"category": "AFRICA", "country": "Ethiopia", "url": "https://addisstandard.com/feed/"},
    # ---- SOUTH ASIA ----
    {"category": "SOUTH ASIA", "country": "India", "url": "http://feeds.feedburner.com/ndtvnews-world-news"},
    {"category": "SOUTH ASIA", "country": "India", "url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"},
    {"category": "SOUTH ASIA", "country": "India", "url": "https://www.thehindu.com/feeder/default.rss"},
    {"category": "SOUTH ASIA", "country": "India", "url": "https://indianexpress.com/feed/"},
    {"category": "SOUTH ASIA", "country": "Pakistan", "url": "https://www.dawn.com/feeds/home"},
    {"category": "SOUTH ASIA", "country": "Pakistan", "url": "https://tribune.com.pk/feed/home"},
    {"category": "SOUTH ASIA", "country": "Bangladesh", "url": "https://www.thedailystar.net/frontpage/rss.xml"},
    {"category": "SOUTH ASIA", "country": "Sri Lanka", "url": "https://www.dailymirror.lk/rss"},
    {"category": "SOUTH ASIA", "country": "Nepal", "url": "https://kathmandupost.com/rss"},
    # ---- EAST ASIA ----
    {"category": "EAST ASIA", "country": "Japan", "url": "https://www.japantimes.co.jp/feed/topstories/"},
    {"category": "EAST ASIA", "country": "Japan", "url": "https://www3.nhk.or.jp/nhkworld/en/news/list/rss.xml"},
    {"category": "EAST ASIA", "country": "South Korea", "url": "https://www.koreatimes.co.kr/www/rss/world.xml"},
    {"category": "EAST ASIA", "country": "South Korea", "url": "https://en.yna.co.kr/RSS/news.xml"},
    {"category": "EAST ASIA", "country": "China", "url": "https://www.cgtn.com/subscribe/rss.html"},
    {"category": "EAST ASIA", "country": "Taiwan", "url": "https://www.taiwannews.com.tw/en/rss/feed.xml"},
    {"category": "EAST ASIA", "country": "Taiwan", "url": "https://www.taipeitimes.com/rss/frontpage.xml"},
    # ---- SOUTHEAST ASIA / OCEANIA ----
    {"category": "SE ASIA / OCEANIA", "country": "Malaysia", "url": "https://www.channelnewsasia.com/rssfeeds/8395986"},
    {"category": "SE ASIA / OCEANIA", "country": "Malaysia", "url": "https://www.malaymail.com/feed/rss/malaysia"},
    {"category": "SE ASIA / OCEANIA", "country": "Philippines", "url": "https://www.inquirer.net/fullfeed"},
    {"category": "SE ASIA / OCEANIA", "country": "Philippines", "url": "https://news.abs-cbn.com/rss/news"},
    {"category": "SE ASIA / OCEANIA", "country": "Indonesia", "url": "https://www.thejakartapost.com/rss"},
    {"category": "SE ASIA / OCEANIA", "country": "Thailand", "url": "https://www.bangkokpost.com/rss/data/topstories.xml"},
    {"category": "SE ASIA / OCEANIA", "country": "Vietnam", "url": "https://vietnamnet.vn/en/rss/news.rss"},
    {"category": "SE ASIA / OCEANIA", "country": "Australia", "url": "https://www.abc.net.au/news/feed/51120/rss.xml"},
    {"category": "SE ASIA / OCEANIA", "country": "Australia", "url": "https://www.smh.com.au/rss/feed.xml"},
    {"category": "SE ASIA / OCEANIA", "country": "Australia", "url": "https://www.sbs.com.au/news/feed"},
    {"category": "SE ASIA / OCEANIA", "country": "New Zealand", "url": "https://www.rnz.co.nz/rss/national"},
    {"category": "SE ASIA / OCEANIA", "country": "Fiji", "url": "https://www.fijitimes.com/feed/"},
    # ---- TECH & FINANCE ----
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://www.marketwatch.com/rss/topstories"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://fortune.com/feed"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://finance.yahoo.com/news/rssindex"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://techcrunch.com/feed/"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://www.theverge.com/rss/index.xml"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://www.wired.com/feed/rss"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://www.cnet.com/rss/news/"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://gizmodo.com/rss"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://news.ycombinator.com/rss"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://www.engadget.com/rss.xml"},
    {"category": "TECH & FINANCE", "country": "United States of America", "url": "https://www.blog.google/rss/"},
    {"category": "TECH & FINANCE", "country": "United Kingdom", "url": "https://www.ft.com/rss/world"},
]

_seen: set[str] = set()
FEEDS: list[dict] = []
for f in RAW_FEEDS:
    if f["url"] not in _seen:
        _seen.add(f["url"])
        FEEDS.append(f)

PER_FEED_QUOTA = 3
MAX_WORKERS = 40
NEWS_CACHE_TTL = 180.0
_YAHOO_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

SYMBOL_REGEX = r"^[A-Z0-9^=./-]{1,15}$"

_NEWS_CACHE: dict = {"data": None, "ts": 0.0}
_PLANES_CACHE: dict = {"data": None, "ts": 0.0}
_PLANES_TTL = 30.0


def _clean_summary(raw: str, limit: int = 240) -> str:
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 3].rstrip() + "..."
    return text or "[No summary available]"


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _classify_sector(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    sectors = {
        "TECH": {"tech", "ai", "software", "chip", "gpu", "crypto", "digital", "web3", "cloud", "startup", "robot"},
        "FINANCE": {"bank", "stock", "market", "finance", "bond", "equity", "inflation", "fed", "economy", "trade"},
        "ENERGY": {"oil", "gas", "energy", "solar", "wind", "power", "crude", "electric", "nuclear"},
        "HEALTH": {"health", "medical", "vaccine", "biotech", "doctor", "pharma", "covid", "disease"},
        "POLITICS": {"election", "government", "policy", "senate", "president", "law", "treaty", "minister", "parliament"},
        "SPORTS": {"sport", "football", "soccer", "nfl", "nba", "cricket", "tennis", "olympic", "match", "league"},
        "CLIMATE": {"climate", "weather", "flood", "quake", "hurricane", "wildfire", "emission"},
    }
    for sector, keywords in sectors.items():
        if any(k in text for k in keywords):
            return sector
    return "GENERAL"


def _fetch_bytes(url: str, timeout: int = 10) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": _YAHOO_UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def _fetch_one(feed: dict) -> list[dict]:
    country = feed.get("country", "")
    category = feed.get("category", "WORLD")
    url = feed["url"]
    try:
        raw = _fetch_bytes(url)
        if raw is None:
            return []
        parsed = feedparser.parse(raw)
        entries = parsed.entries[:PER_FEED_QUOTA] if parsed.entries else []
        if not entries:
            return []
        out: list[dict] = []
        for entry in entries:
            title = entry.get("title") or "Untitled"
            if isinstance(title, list):
                title = str(title[0]) if title else "Untitled"
            title = str(title).strip()
            link = entry.get("link") or url
            if isinstance(link, list):
                link = link[0] if link else url
            link = str(link)
            summary_raw = entry.get("summary") or entry.get("description") or ""
            if isinstance(summary_raw, list):
                summary_raw = str(summary_raw[0]) if summary_raw else ""
            summary_raw = str(summary_raw)
            published = entry.get("published") or entry.get("updated") or ""
            out.append({
                "category": category,
                "country": country,
                "title": title,
                "link": link,
                "summary": _clean_summary(summary_raw),
                "sector": _classify_sector(title, summary_raw),
                "source": _domain(link) or _domain(url),
                "published": str(published),
            })
        return out
    except Exception:
        return []


@app.get("/news")
def get_news(limit: int = None, custom_feeds: str = None, countries: str = None, sectors: str = None):
    now = time.time()
    active_feeds = FEEDS
    if custom_feeds:
        urls = [u.strip() for u in custom_feeds.split(",") if u.strip()]
        custom_list = [{"category": "CUSTOM", "country": "Custom", "url": u} for u in urls]
        active_feeds = FEEDS + custom_list

    use_cache = _NEWS_CACHE["data"] is not None and (now - _NEWS_CACHE["ts"]) < NEWS_CACHE_TTL and not custom_feeds and not countries and not sectors and limit is None
    if use_cache:
        data = _NEWS_CACHE["data"]
    else:
        feeds_to_fetch = active_feeds
        is_partial = False
        if limit is not None and _NEWS_CACHE["data"] is None and not custom_feeds and not countries and not sectors:
            feeds_to_fetch = active_feeds[: max(limit * 2, 20)]
            is_partial = True

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            results = list(pool.map(_fetch_one, feeds_to_fetch))
        stories: list[dict] = []
        seen_links: set[str] = set()
        for batch in results:
            for s in batch:
                # skip error placeholders, dedupe by link
                if not s.get("title") or s["title"].startswith("[ Feed"):
                    continue
                if s["link"] in seen_links:
                    continue
                seen_links.add(s["link"])
                stories.append(s)

        if not custom_feeds and not countries and not sectors and not is_partial:
            _NEWS_CACHE["data"] = stories
            _NEWS_CACHE["ts"] = now
        data = stories

    # server-side filters (used by world map + customize tab)
    if countries:
        wanted = {c.strip().lower() for c in countries.split(",") if c.strip()}
        data = [s for s in data if (s.get("country") or "").lower() in wanted]
    if sectors:
        wanted_s = {c.strip().upper() for c in sectors.split(",") if c.strip()}
        data = [s for s in data if (s.get("sector") or "GENERAL").upper() in wanted_s]

    if limit is not None:
        return data[:limit]
    return data


@app.get("/news/feeds")
def list_feeds():
    cats: dict[str, list] = {}
    for f in FEEDS:
        cats.setdefault(f["category"], []).append({"country": f["country"], "url": f["url"]})
    countries = sorted({f["country"] for f in FEEDS})
    return {"total": len(FEEDS), "countries": countries, "by_category": cats}


@app.get("/news/countries")
def news_by_country():
    data = _NEWS_CACHE.get("data") or []
    counts: dict[str, int] = {}
    for s in data:
        c = s.get("country") or "Unknown"
        counts[c] = counts.get(c, 0) + 1
    return [{"country": k, "stories": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


@app.get("/crypto/status")
def get_crypto_status():
    gas_url = "https://api.etherscan.io/api?module=gastracker&action=gasoracle"
    trending_url = "https://api.coingecko.com/api/v3/search/trending"
    res_gas = {}
    res_trending = []
    try:
        body_gas = urllib.request.urlopen(gas_url, timeout=5).read()
        data_gas = json.loads(body_gas)
        res_gas = data_gas.get("result", {})
    except Exception:
        pass
    try:
        body_trend = urllib.request.urlopen(trending_url, timeout=5).read()
        data_trend = json.loads(body_trend)
        res_trending = [c["item"]["name"] for c in data_trend.get("coins", [])[:5]]
    except Exception:
        pass
    return {"gas_price": res_gas.get("ProposeGasPrice", "—"), "trending": res_trending}


@app.get("/stocks/search")
def search_stocks(q: str):
    query = q.strip()
    if not query:
        return []
    url = (
        "https://query1.finance.yahoo.com/v1/finance/search?"
        + urllib.parse.urlencode({"q": query, "quotesCount": 10, "newsCount": 0, "listsCount": 0})
    )
    req = urllib.request.Request(url, headers={"User-Agent": _YAHOO_UA})
    try:
        body = urllib.request.urlopen(req, timeout=10).read()
        data = json.loads(body)
        quotes = data.get("quotes") or []
        out = []
        for q_ in quotes:
            symbol = q_.get("symbol")
            if not symbol or not re.match(SYMBOL_REGEX, symbol.upper()):
                continue
            out.append({
                "symbol": symbol.upper(),
                "name": q_.get("shortname") or q_.get("longname") or symbol,
                "quoteType": q_.get("quoteType", "UNKNOWN"),
                "exchange": q_.get("exchange", "UNKNOWN"),
            })
        return out
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search failed: {exc}")


@app.get("/weather")
def get_weather(lat: float, lon: float):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        body = urllib.request.urlopen(url, timeout=10).read()
        return json.loads(body).get("current_weather", {})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather fetch failed: {exc}")


@app.get("/global/alerts")
def get_global_alerts():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson"
    try:
        body = urllib.request.urlopen(url, timeout=10).read()
        data = json.loads(body)
        alerts = []
        for feature in data.get("features", [])[:8]:
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [0, 0])
            alerts.append({
                "mag": props.get("mag"),
                "place": props.get("place"),
                "time": props.get("time"),
                "url": props.get("url"),
                "lat": coords[1],
                "lon": coords[0],
            })
        return alerts
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"USGS fetch failed: {exc}")


@app.get("/stocks/{symbol}")
def get_stocks(symbol: str, range: str = "1y", interval: str = "1d"):
    sym = symbol.strip().upper()
    if not re.match(SYMBOL_REGEX, sym):
        raise HTTPException(status_code=400, detail="Invalid symbol format")

    valid_ranges = {"1d", "5d", "1mo", "3mo", "1y", "max"}
    if range not in valid_ranges:
        range = "1y"

    intervals = {"1d": "5m", "5d": "15m", "1mo": "1h", "3mo": "1d", "1y": "1d", "max": "1wk"}
    interval = intervals[range]

    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(sym, safe="^")
        + f"?range={range}&interval={interval}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": _YAHOO_UA})
    try:
        body = urllib.request.urlopen(req, timeout=15).read()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"yahoo fetch failed: {exc}")
    try:
        payload = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"yahoo parse failed: {exc}")
    result = (payload.get("chart") or {}).get("result")
    if not result:
        err = (payload.get("chart") or {}).get("error") or {}
        raise HTTPException(status_code=502, detail=f"yahoo returned no result: {err.get('description', '')}")
    r = result[0]
    m = r.get("meta") or {}
    q = ((r.get("indicators") or {}).get("quote") or [{}])[0]
    timestamps = r.get("timestamp") or []
    closes_raw = q.get("close") or []
    opens_raw = q.get("open") or []
    highs_raw = q.get("high") or []
    lows_raw = q.get("low") or []
    vols_raw = q.get("volume") or []

    last = m.get("regularMarketPrice")
    prev = m.get("chartPreviousClose")
    # fallback: derive from series when meta missing
    valid_closes = [c for c in closes_raw if c is not None]
    if last is None and valid_closes:
        last = valid_closes[-1]
    if prev is None and len(valid_closes) >= 2:
        prev = valid_closes[-2]
    change = (last - prev) if (last is not None and prev is not None) else None
    change_pct = (change / prev * 100.0) if (change is not None and prev not in (None, 0)) else None

    def safe(arr, idx):
        a = len(arr)
        if not (-a <= idx < a):
            return None
        v = arr[idx]
        return v if v is not None else None

    # find last valid index
    last_idx = len(closes_raw) - 1
    while last_idx >= 0 and closes_raw[last_idx] is None:
        last_idx -= 1

    day_open = safe(opens_raw, last_idx)
    day_high = safe(highs_raw, last_idx)
    day_low = safe(lows_raw, last_idx)
    day_vol = safe(vols_raw, last_idx)

    closes_52w = [c for c in closes_raw if c is not None]
    highs_52w = [h for h in highs_raw if h is not None]
    lows_52w = [l for l in lows_raw if l is not None]

    if range == "1d":
        fmt = "%H:%M"
    elif range in ("5d", "1mo"):
        fmt = "%b %d %H:%M"
    else:
        fmt = "%Y-%m-%d"

    gmt_offset = m.get("gmtoffset") or 0

    history: list[dict] = []
    for i, ts in enumerate(timestamps):
        c = closes_raw[i] if i < len(closes_raw) else None
        if c is None:
            continue
        local_ts = ts + gmt_offset
        history.append({
            "date": time.strftime(fmt, time.gmtime(local_ts)),
            "close": round(float(c), 4),
            "open": round(float(safe(opens_raw, i)), 4) if safe(opens_raw, i) is not None else None,
            "high": round(float(safe(highs_raw, i)), 4) if safe(highs_raw, i) is not None else None,
            "low": round(float(safe(lows_raw, i)), 4) if safe(lows_raw, i) is not None else None,
            "volume": safe(vols_raw, i),
        })

    summary_url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(sym, safe='^=')}?modules=defaultKeyStatistics,financialData,summaryDetail,price"
    summary_req = urllib.request.Request(summary_url, headers={"User-Agent": _YAHOO_UA})
    summary_data = {}
    try:
        summary_body = urllib.request.urlopen(summary_req, timeout=10).read()
        summary_json = json.loads(summary_body)
        res_sum = summary_json.get("quoteSummary", {}).get("result", [{}])[0]
        summary_data = res_sum
    except Exception:
        pass

    def get_sum(module, key):
        try:
            return summary_data.get(module, {}).get(key, {}).get("raw", "—")
        except Exception:
            return "—"

    return {
        "symbol": sym,
        "name": m.get("longName") or m.get("shortName") or sym,
        "exchange": m.get("exchangeName") or m.get("fullExchangeName"),
        "currency": m.get("currency"),
        "last": last,
        "previousClose": prev,
        "change": (round(change, 4) if change is not None else None),
        "changePct": (round(change_pct, 3) if change_pct is not None else None),
        "dayOpen": day_open,
        "dayHigh": day_high,
        "dayLow": day_low,
        "volume": day_vol,
        "fiftyTwoHigh": m.get("fiftyTwoWeekHigh") or (max(highs_52w) if highs_52w else None),
        "fiftyTwoLow": m.get("fiftyTwoWeekLow") or (min(lows_52w) if lows_52w else None),
        "history": history,
        "metrics": {
            "pe": get_sum("defaultKeyStatistics", "trailingPE"),
            "marketCap": get_sum("defaultKeyStatistics", "marketCap"),
            "dividend": get_sum("summaryDetail", "dividendYield"),
        },
    }


@app.get("/finance/indicators")
def get_finance_indicators():
    symbols = {
        "COMMODITIES": ["GC=F", "SI=F", "CL=F", "NG=F"],
        "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"],
        "CURRENCIES": ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "USDCNY=X"],
        "BONDS": ["^TNX", "^FVX"],
        "INDICES": ["^GSPC", "^DJI", "^IXIC", "^FTSE"],
    }
    results = {k: [] for k in symbols}
    req_headers = {"User-Agent": _YAHOO_UA}
    for category, syms in symbols.items():
        for sym in syms:
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym, safe='^=')}?range=5d&interval=1d"
                req = urllib.request.Request(url, headers=req_headers)
                body = urllib.request.urlopen(req, timeout=5).read()
                payload = json.loads(body)
                r = (payload.get("chart") or {}).get("result")
                if r:
                    meta = r[0].get("meta") or {}
                    quote = (r[0].get("indicators") or {}).get("quote", [{}])[0]
                    history = [x for x in (quote.get("close", []) or []) if x is not None]
                    last = meta.get("regularMarketPrice")
                    prev = meta.get("chartPreviousClose")
                    if last is None and history:
                        last = history[-1]
                    if prev is None and len(history) >= 2:
                        prev = history[-2]
                    change = (last - prev) if (last is not None and prev is not None) else 0
                    pct = (change / prev * 100.0) if (prev not in (None, 0)) else 0
                    results[category].append({
                        "symbol": sym,
                        "name": meta.get("shortName") or meta.get("longName") or sym,
                        "last": last,
                        "change": round(change, 4) if change else 0,
                        "changePct": round(pct, 3) if pct else 0,
                        "history": history,
                    })
            except Exception:
                continue
    return results


@app.get("/weather/full")
def get_weather_full(lat: float, lon: float):
    """Fetches forecast, AQI, and UV index for a location."""
    forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max&timezone=auto"
    aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide"
    data = {"forecast": {}, "aqi": {}, "location": {"lat": lat, "lon": lon}}
    try:
        body = urllib.request.urlopen(forecast_url, timeout=10).read()
        data["forecast"] = json.loads(body)
    except Exception:
        pass
    try:
        body = urllib.request.urlopen(aqi_url, timeout=10).read()
        data["aqi"] = json.loads(body)
    except Exception:
        pass
    return data


# Correct ESPN sport/league paths. Old code used bare "soccer" which 404s.
ESPN_SPORTS = [
    ("football", "nfl"),
    ("basketball", "nba"),
    ("baseball", "mlb"),
    ("hockey", "nhl"),
    ("basketball", "wnba"),
    ("soccer", "eng.1"),
    ("soccer", "esp.1"),
    ("soccer", "ger.1"),
    ("soccer", "ita.1"),
    ("soccer", "fra.1"),
    ("soccer", "usa.1"),
    ("soccer", "uefa.champions"),
    ("football", "college-football"),
    ("basketball", "mens-college-basketball"),
    ("mma", "ufc"),
    ("tennis", "atp"),
    ("golf", "pga"),
]


@app.get("/sports/scoreboard")
def get_sports_scoreboard(league: str = None):
    targets = ESPN_SPORTS
    if league:
        # allow ?league=nba or ?league=eng.1
        targets = [t for t in ESPN_SPORTS if league.lower() in (t[0], t[1]) or f"{t[0]}/{t[1]}" == league.lower()]
        if not targets:
            targets = ESPN_SPORTS

    def fetch_one(pair):
        sport, lg = pair
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{lg}/scoreboard"
            req = urllib.request.Request(url, headers={"User-Agent": _YAHOO_UA})
            body = urllib.request.urlopen(req, timeout=6).read()
            payload = json.loads(body)
            out = []
            for event in payload.get("events", [])[:10]:
                comp = (event.get("competitions") or [{}])[0]
                competitors = comp.get("competitors", [])
                home = next((c for c in competitors if c.get("homeAway") == "home"), {})
                away = next((c for c in competitors if c.get("homeAway") == "away"), {})
                status = event.get("status", {}) or {}
                stype = status.get("type", {}) or {}
                venue = (comp.get("venue") or {}).get("fullName", "")
                broadcast = ", ".join([b.get("names", [""])[0] for b in (comp.get("broadcasts", []) or []) if b.get("names")][:2])

                def team_info(t):
                    tm = t.get("team", {}) or {}
                    recs = t.get("records", []) or []
                    rec = recs[0].get("summary", "") if recs else ""
                    return {
                        "abbr": tm.get("abbreviation", "TBD"),
                        "name": tm.get("displayName", tm.get("shortDisplayName", "TBD")),
                        "logo": tm.get("logo", ""),
                        "color": tm.get("color", "33ff33"),
                        "score": t.get("score", "0"),
                        "record": rec,
                        "winner": bool(t.get("winner", False)),
                    }

                link_map: dict[str, str] = {}
                for L in (event.get("links") or []):
                    rels = L.get("rel") or [""]
                    href = L.get("href", "")
                    if href and rels[0] not in link_map:
                        link_map[rels[0]] = href
                out.append({
                    "league": f"{sport}/{lg}".upper(),
                    "league_short": lg.upper(),
                    "name": event.get("name"),
                    "short_name": event.get("shortName", event.get("name")),
                    "status": stype.get("description", stype.get("shortDetail", "Scheduled")),
                    "detail": stype.get("shortDetail", ""),
                    "state": stype.get("state", ""),
                    "time": event.get("date"),
                    "venue": venue,
                    "broadcast": broadcast,
                    "url": link_map.get("gamecast") or link_map.get("live") or link_map.get("summary") or (next(iter(link_map.values())) if link_map else ""),
                    "boxscore": link_map.get("boxscore", ""),
                    "home": team_info(home),
                    "away": team_info(away),
                    # back-compat flat fields for old frontend
                    "home_team": (home.get("team") or {}).get("abbreviation", "TBD"),
                    "home_score": home.get("score", "0"),
                    "away_team": (away.get("team") or {}).get("abbreviation", "TBD"),
                    "away_score": away.get("score", "0"),
                })
            return out
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(fetch_one, targets))
    all_events: list[dict] = []
    for batch in results:
        all_events.extend(batch)
    # live/in-progress first, then the rest
    def rank(e):
        st = (e.get("state") or "").lower()
        if st == "in":
            return 0
        return 1
    all_events.sort(key=rank)
    return all_events[:40]


@app.get("/sports/leagues")
def list_sports_leagues():
    return [{"sport": s, "league": lg, "label": f"{s}/{lg}"} for s, lg in ESPN_SPORTS]


@app.get("/planes/global")
def get_planes_global(limit: int = 300, lamin: float = None, lamax: float = None, lomin: float = None, lomax: float = None):
    now = time.time()
    use_cache = (
        _PLANES_CACHE["data"] is not None
        and (now - _PLANES_CACHE["ts"]) < _PLANES_TTL
        and lamin is None
    )
    if use_cache:
        data = _PLANES_CACHE["data"]
        return data[:limit]

    if lamin is not None and lamax is not None and lomin is not None and lomax is not None:
        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"
    else:
        url = "https://opensky-network.org/api/states/all"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _YAHOO_UA})
        # OpenSky can be slow; allow longer timeout but fail gracefully
        body = urllib.request.urlopen(req, timeout=25).read()
        data = json.loads(body)
        flights = []
        states = data.get("states", []) or []
        for state in states:
            try:
                lon = state[5]
                lat = state[6]
                if lon is None or lat is None:
                    continue
                if not (-180 <= float(lon) <= 180 and -90 <= float(lat) <= 90):
                    continue
                alt_m = state[7]
                vel_ms = state[9]
                flights.append({
                    "icao24": state[0],
                    "callsign": (state[1] or "N/A").strip() or "N/A",
                    "country": state[2] or "Unknown",
                    "lon": float(lon),
                    "lat": float(lat),
                    "altitude_m": alt_m,
                    "altitude_ft": round(float(alt_m) * 3.28084) if alt_m is not None else None,
                    "velocity_ms": vel_ms,
                    "velocity_kmh": round(float(vel_ms) * 3.6) if vel_ms is not None else None,
                    "velocity_kts": round(float(vel_ms) * 1.94384) if vel_ms is not None else None,
                    "heading": state[10],
                    "vertical_rate": state[11] if len(state) > 11 else None,
                    "on_ground": bool(state[8]) if len(state) > 8 else False,
                    "squawk": state[14] if len(state) > 14 else None,
                })
            except Exception:
                continue
        # most interesting first: airborne, high altitude
        flights.sort(key=lambda f: (f["on_ground"], -(f["altitude_m"] or 0)))
        if lamin is None:
            _PLANES_CACHE["data"] = flights
            _PLANES_CACHE["ts"] = now
        return flights[:limit]
    except Exception as exc:
        # serve stale cache if available
        if _PLANES_CACHE["data"]:
            return _PLANES_CACHE["data"][:limit]
        raise HTTPException(status_code=502, detail=f"OpenSky fetch failed: {exc}")


# Serve the frontend (index.html) as a real website at "/"
# MUST be registered AFTER all API routes, otherwise it shadows them with 404
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6767)
