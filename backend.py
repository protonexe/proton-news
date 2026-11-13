import calendar
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
from fastapi.responses import RedirectResponse
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
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://feeds.content.dowjones.io/public/rss/RSSUSNews"},
    {"category": "NORTH AMERICA", "country": "United States of America", "url": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"},
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
MAX_STORY_AGE_HOURS = 24 * 14  # drop stale items (dead/frozen feeds) older than 2 weeks
_YAHOO_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

SYMBOL_REGEX = r"^[A-Z0-9^=./-]{1,15}$"

_NEWS_CACHE: dict = {"data": None, "ts": 0.0}
_QUICK_CACHE: dict = {"data": None, "ts": 0.0}
_QUICK_TTL = 300.0
_CRYPTO_CACHE: dict = {"data": None, "ts": 0.0}
_CRYPTO_TTL = 300.0
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


def _team_logo(tm: dict) -> str:
    """Best-effort team logo URL across ESPN shapes (logo str / logos list)."""
    if not isinstance(tm, dict):
        return ""
    v = tm.get("logo")
    if isinstance(v, str) and v.strip():
        return v.strip()
    logos = tm.get("logos") or []
    if isinstance(logos, dict):
        logos = [logos]
    if isinstance(logos, list):
        for lg in logos:
            if isinstance(lg, dict):
                href = lg.get("href") or lg.get("url") or ""
                if isinstance(href, str) and href.strip():
                    return href.strip()
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


def _entry_ts(entry: dict) -> float:
    """Published timestamp as epoch seconds (0 when the feed omits a date)."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        st = entry.get(key)
        if not st:
            continue
        try:
            return float(calendar.timegm(st))
        except Exception:
            continue
    return 0.0


def _fresh_dedupe(stories: list[dict]) -> list[dict]:
    """Drop stale + duplicate headlines, newest first."""
    now = time.time()
    cutoff = now - MAX_STORY_AGE_HOURS * 3600
    out: list[dict] = []
    seen_titles: set[str] = set()
    for s in stories:
        ts = float(s.get("ts") or 0)
        if ts:
            if ts < cutoff:
                continue
            if ts > now + 86400:  # tolerate timezone-damaged dates
                ts = now
                s["ts"] = ts
        key = re.sub(r"[^a-z0-9]", "", (s.get("title") or "").lower())[:90]
        if key and key in seen_titles:
            continue
        seen_titles.add(key)
        out.append(s)
    out.sort(key=lambda x: float(x.get("ts") or 0), reverse=True)
    return out


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
            image = ""
            try:
                for th in (entry.get("media_thumbnail") or []):
                    if isinstance(th, dict) and th.get("url"):
                        image = str(th["url"])
                        break
                if not image:
                    for mc in (entry.get("media_content") or []):
                        u = mc.get("url", "") if isinstance(mc, dict) else ""
                        if isinstance(u, str) and re.search(r"\.(jpe?g|png|webp|gif)(\?|$)", u, re.I):
                            image = u
                            break
                if not image:
                    for ln in (entry.get("links") or []):
                        if isinstance(ln, dict) and ln.get("rel") == "enclosure" \
                                and "image" in str(ln.get("type", "")) and ln.get("href"):
                            image = str(ln["href"])
                            break
            except Exception:
                image = ""
            out.append({
                "category": category,
                "country": country,
                "title": title,
                "link": link,
                "summary": _clean_summary(summary_raw),
                "sector": _classify_sector(title, summary_raw),
                "source": _domain(link) or _domain(url),
                "published": str(published),
                "ts": _entry_ts(entry),
                "image": image,
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

        stories = _fresh_dedupe(stories)

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


@app.get("/news/quick")
def get_news_quick(limit: int = 60):
    """Small fast subset for the dash demos (own cache, never blocks /news)."""
    now = time.time()
    if _QUICK_CACHE["data"] is not None and (now - _QUICK_CACHE["ts"]) < _QUICK_TTL:
        return _QUICK_CACHE["data"][:limit]
    feeds = FEEDS[:60]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = list(pool.map(_fetch_one, feeds))
    stories: list[dict] = []
    seen: set[str] = set()
    for batch in results:
        for s in batch:
            if not s.get("title") or s["link"] in seen:
                continue
            seen.add(s["link"])
            stories.append(s)
    stories = _fresh_dedupe(stories)
    _QUICK_CACHE["data"] = stories
    _QUICK_CACHE["ts"] = now
    return stories[:limit]


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


@app.get("/crypto/markets")
def get_crypto_markets(limit: int = 15):
    now = time.time()
    if _CRYPTO_CACHE["data"] is not None and (now - _CRYPTO_CACHE["ts"]) < _CRYPTO_TTL:
        data = _CRYPTO_CACHE["data"]
    else:
        url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
               "&order=market_cap_desc&per_page=25&page=1&sparkline=false"
               "&price_change_percentage=1h,24h,7d")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _YAHOO_UA})
            body = urllib.request.urlopen(req, timeout=15).read()
            raw = json.loads(body)
        except Exception as exc:
            if _CRYPTO_CACHE["data"] is not None:
                data = _CRYPTO_CACHE["data"]
            else:
                raise HTTPException(status_code=502, detail=f"CoinGecko failed: {exc}")
        else:
            data = [{
                "rank": c.get("market_cap_rank"),
                "symbol": (c.get("symbol") or "").upper(),
                "name": c.get("name"),
                "image": c.get("image"),
                "price": c.get("current_price"),
                "chg1h": c.get("price_change_percentage_1h_in_currency"),
                "chg24h": (c.get("price_change_percentage_24h_in_currency")
                           if c.get("price_change_percentage_24h_in_currency") is not None
                           else c.get("price_change_percentage_24h")),
                "chg7d": c.get("price_change_percentage_7d_in_currency"),
                "mcap": c.get("market_cap"),
                "volume": c.get("total_volume"),
            } for c in (raw or [])]
            _CRYPTO_CACHE["data"] = data
            _CRYPTO_CACHE["ts"] = now
    return data[: max(limit, 1)]


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
                        "logo": _team_logo(tm),
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
                    "gid": event.get("id"),
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


@app.get("/sports/standings")
def get_sports_standings(sport: str = "basketball", league: str = "nba"):
    sport = sport.strip().lower()
    league = league.strip().lower()
    if not any(s == sport and lg == league for s, lg in ESPN_SPORTS):
        raise HTTPException(status_code=400, detail="Unknown sport/league")
    url = f"https://site.web.api.espn.com/apis/v2/sports/{sport}/{league}/standings"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _YAHOO_UA})
        body = urllib.request.urlopen(req, timeout=8).read()
        payload = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ESPN standings failed: {exc}")

    def stat_map(entry):
        m: dict[str, str] = {}
        for s in (entry.get("stats") or []):
            v = s.get("displayValue", s.get("value", ""))
            if v is None:
                v = ""
            m[s.get("name", "")] = str(v)
        return m

    groups = []
    for child in payload.get("children", []) or []:
        rows = []
        for entry in ((child.get("standings") or {}).get("entries") or []):
            tm = entry.get("team") or {}
            sm = stat_map(entry)
            rows.append({
                "team": tm.get("displayName", tm.get("shortDisplayName", "?")),
                "abbr": tm.get("abbreviation", "?"),
                "logo": _team_logo(tm),
                "w": sm.get("wins", ""),
                "l": sm.get("losses", ""),
                "t": sm.get("ties", ""),
                "pts": sm.get("points", ""),
                "pct": sm.get("winPercent") or sm.get("leagueWinPercent", ""),
                "gb": sm.get("gamesBehind", ""),
                "streak": sm.get("streak", ""),
                "rank": sm.get("rank", ""),
                "gf": sm.get("pointsFor", ""),
                "ga": sm.get("pointsAgainst", ""),
                "diff": sm.get("pointDifferential") or sm.get("differential", ""),
            })
        groups.append({"name": child.get("name", "Standings"), "rows": rows})
    return {"sport": sport, "league": league, "season": (payload.get("season") or {}).get("year"), "groups": groups}


@app.get("/planes/global")
def get_planes_global(limit: int = 300, lamin: float = None, lamax: float = None, lomin: float = None, lomax: float = None, spread: int = 0):
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
        if spread:
            # geographically-even sample so the map paints the whole world
            # instead of only the 300 highest aircraft.
            import random as _random
            pool = list(flights)
            _random.Random(7).shuffle(pool)
            picked: list[dict] = []
            per_cell: dict[tuple[int, int], int] = {}
            for f in pool:
                cell = (int(f["lat"] // 10), int(f["lon"] // 10))
                if per_cell.get(cell, 0) >= 3:
                    continue
                per_cell[cell] = per_cell.get(cell, 0) + 1
                picked.append(f)
                if len(picked) >= limit:
                    break
            return picked
        return flights[:limit]
    except Exception as exc:
        # serve stale cache if available
        if _PLANES_CACHE["data"]:
            return _PLANES_CACHE["data"][:limit]
        raise HTTPException(status_code=502, detail=f"OpenSky fetch failed: {exc}")


# ---------------------------------------------------------------- article text
# /article/extract pulls the full readable body out of the publisher page so the
# dash reader can show the actual story instead of only the RSS summary.
# Bodies are cached in memory and on disk so restarts stay warm and
# /article/search can query everything that has ever been opened.
import hashlib
import threading
from urllib.error import HTTPError

_ARTICLE_CACHE: dict = {}
_ARTICLE_TTL = 12 * 3600.0
_ARTICLE_MAX = 400

_DISK_TTL = 3 * 86400.0
_DISK_MAX = 1200
_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cache", "articles"
)
_DOMAIN_GAP = 1.2  # seconds between requests to the same publisher
_domain_last: dict[str, float] = {}
_cache_lock = threading.Lock()
_disk_writes = 0

_UA_ARTICLE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _disk_path(url: str) -> str:
    return os.path.join(_CACHE_DIR, hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json")


def _disk_get(url: str) -> dict | None:
    try:
        with open(_disk_path(url), "r", encoding="utf-8") as fh:
            rec = json.load(fh)
        if (
            isinstance(rec, dict)
            and isinstance(rec.get("data"), dict)
            and (time.time() - float(rec.get("ts") or 0)) < _DISK_TTL
        ):
            return rec
    except Exception:
        pass
    return None


def _disk_put(url: str, data: dict) -> None:
    global _disk_writes
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        path = _disk_path(url)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(
                {"ts": time.time(), "url": url, "data": data},
                fh,
                ensure_ascii=False,
            )
        os.replace(tmp, path)
    except Exception:
        return
    _disk_writes += 1
    if _disk_writes % 25 == 0:
        _disk_prune()


def _disk_prune() -> None:
    try:
        names = [n for n in os.listdir(_CACHE_DIR) if n.endswith(".json")]
        if len(names) <= _DISK_MAX:
            return
        paths = [os.path.join(_CACHE_DIR, n) for n in names]
        paths.sort(key=lambda p: os.path.getmtime(p))
        for p in paths[: len(paths) - _DISK_MAX]:
            try:
                os.remove(p)
            except OSError:
                pass
    except Exception:
        pass


def _rate_limit(host: str) -> None:
    """Keep at most one request every _DOMAIN_GAP seconds per publisher."""
    if not host:
        return
    with _cache_lock:
        now = time.time()
        last = _domain_last.get(host, 0.0)
        _domain_last[host] = max(now, last + _DOMAIN_GAP)
        wait = _DOMAIN_GAP - (now - last)
    if wait > 0:
        time.sleep(min(wait, 4.0))


_BOILER_RE = re.compile(
    r"(subscribe|sign up|newsletter|cookies?|privacy policy|terms of (use|service)|"
    r"all rights reserved|advertis(e|ement)|follow us|share (this|on)|read more|"
    r"click here|download (the|our) app|©|copyright|support our journalism|"
    r"become a member|already a subscriber|get the latest|stay (up to date|informed)|"
    r"related (articles?|stories)|photo(graph)? (by|credit)|getty images|"
    r"see more of our coverage|your search results|click to share|copy link|"
    r"email to a friend|skip advert|recommended (for you|stories)|most popular|"
    r"read next|you may also like|listen to (this|the) article|"
    r"apple podcasts|google podcasts|spotify|ivoox|podimo|"
    r"esc[uú]chalo|puedes escucharlo|"
    r"this (article|story) (was|has been) originally)",
    re.I,
)

# Publisher paywall markers. Kept separate from boilerplate because hitting one
# means the body is truncated, which the reader should say out loud.
_PAYWALL_RE = re.compile(
    r"(il (vous )?reste\s+\d+(?:[.,]\d+)?\s*%|la suite est r[ée]serv[ée]e|"
    r"subscribe (to|for) (continue|full access)|to continue reading|"
    r"this (article|story) is (only )?available (to|for) subscribers|"
    r"for subscribers only|become a subscriber|"
    r"rest of (this|the) (article|story)|continue reading (with|on)|"
    r"already a subscriber\??\s*(sign|log) in|unlock (this|the) article|"
    r"este (art[ií]culo|contenido) es (solo )?para suscriptores|"
    r"suscr[ií]bete para (seguir|continuar)|contenido exclusivo para suscriptores|"
    r"nur f[uü]r abonnenten|weiterlesen mit|"
    r"conte[uú]do exclusivo para assinantes|assine para (continuar|ler))",
    re.I,
)


def _article_meta(html_text: str) -> dict:
    """Pull og/meta tags regardless of attribute order."""
    out: dict = {}
    for tag in re.findall(r"<meta\b[^>]*>", html_text or "", re.I):
        attrs = dict(
            (k.lower(), v)
            for k, v in re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', tag)
        )
        attrs.update(
            dict((k.lower(), v) for k, v in re.findall(r"([\w:-]+)\s*=\s*'([^']*)'", tag))
        )
        key = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
        val = attrs.get("content")
        if key and val:
            out.setdefault(key.lower(), unescape(val).strip())
    return out


def _article_paras(text: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for chunk in re.split(r"\n+", text or ""):
        p = re.sub(r"\s+", " ", chunk).strip()
        if len(p) < 45 or len(p.split()) < 7:
            continue
        # drop short boilerplate lines only; long prose that happens to mention
        # "subscribe" is real copy and must survive
        if len(p) < 170 and _BOILER_RE.search(p):
            continue
        key = re.sub(r"[^a-z0-9 ]", "", p.lower())[:120]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _jsonld_body(html_text: str) -> str:
    for m in re.finditer(
        r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html_text or "", re.S | re.I
    ):
        try:
            data = json.loads(unescape(m.group(1)).strip())
        except Exception:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
                continue
            if not isinstance(node, dict):
                continue
            if isinstance(node.get("@graph"), list):
                stack.extend(node["@graph"])
            body = node.get("articleBody")
            if isinstance(body, str) and len(body) > 400:
                return body
    return ""


def _heuristic_body(html_text: str) -> list[str]:
    """Fallback reader: score containers by prose length minus link density."""
    try:
        from lxml import html as LH
    except Exception:
        return []
    try:
        doc = LH.fromstring(html_text)
    except Exception:
        return []
    for bad in doc.xpath("//script|//style|//noscript|//nav|//footer|//aside|//form|//iframe|//svg"):
        parent = bad.getparent()
        if parent is not None:
            parent.remove(bad)
    best = None
    best_score = 0.0
    for el in doc.xpath("//article|//main|//*[@role='main']|//section|//div"):
        ps = el.xpath(".//p")
        if len(ps) < 2:
            continue
        prose = sum(len(re.sub(r"\s+", " ", "".join(p.itertext())).strip()) for p in ps)
        link_chars = sum(len("".join(a.itertext())) for a in el.xpath(".//a"))
        score = prose - link_chars * 1.6
        if score > best_score:
            best_score, best = score, el
    if best is None:
        return []
    raw = "\n".join(
        re.sub(r"\s+", " ", "".join(p.itertext())).strip() for p in best.xpath(".//p")
    )
    return _article_paras(raw)


def _fetch_article_html(url: str, tries: int = 2) -> tuple[str, str]:
    host = (urlparse(url).hostname or "").lower()
    last_exc: Exception | None = None
    for attempt in range(tries):
        _rate_limit(host)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": _UA_ARTICLE,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=18) as resp:
                raw = resp.read(3_000_000)
                charset = resp.headers.get_content_charset()
                final = resp.geturl()
            return _decode_html(raw, charset), final
        except HTTPError as exc:
            last_exc = exc
            if exc.code in (429, 503) and attempt + 1 < tries:
                time.sleep(2.0 + attempt * 2.0)
                continue
            raise
        except Exception as exc:
            last_exc = exc
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("article fetch failed")



def _decode_html(raw: bytes, charset: str | None) -> str:
    """Honour header charset, then <meta charset>, then sniff. Feeds are global,
    so a hard utf-8 default mangles curly quotes on older CMS output."""
    if charset:
        try:
            return raw.decode(charset, errors="replace")
        except LookupError:
            pass
    head = raw[:8192].decode("ascii", errors="ignore")
    m = re.search(r'<meta[^>]+charset\s*=\s*["\']?([\w-]+)', head, re.I)
    if m:
        try:
            return raw.decode(m.group(1), errors="replace")
        except LookupError:
            pass
    try:
        from charset_normalizer import from_bytes

        best = from_bytes(raw).best()
        if best is not None:
            return str(best)
    except Exception:
        pass
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def _extract_article(url: str) -> dict:
    html_text, final_url = _fetch_article_html(url)
    meta = _article_meta(html_text)
    host = urlparse(final_url).hostname or ""
    site = (meta.get("og:site_name") or host.replace("www.", "")).strip()

    candidates: list[tuple[str, list[str]]] = []

    # 1) trafilatura — best general-purpose reader
    try:
        import trafilatura

        raw = trafilatura.extract(
            html_text,
            url=final_url,
            output_format="json",
            include_comments=False,
            include_tables=False,
            favor_recall=True,
            with_metadata=True,
        )
        if raw:
            payload = json.loads(raw)
            text = payload.get("text") or ""
            paras = _article_paras(text)
            if paras:
                candidates.append(("trafilatura", paras))
                meta.setdefault("title", payload.get("title") or "")
                meta.setdefault("author", payload.get("author") or "")
                meta.setdefault("date", payload.get("date") or "")
                meta.setdefault("image", payload.get("image") or "")
                site = (payload.get("sitename") or site).strip()
    except Exception:
        pass

    # 2) structured data articleBody
    ld = _jsonld_body(html_text)
    if ld:
        paras = _article_paras(ld)
        if paras:
            candidates.append(("json-ld", paras))

    # 3) DOM heuristic
    heur = _heuristic_body(html_text)
    if heur:
        candidates.append(("heuristic", heur))

    if not candidates:
        return {}
    # trafilatura is the cleanest source. Use it whenever it produced a real
    # body; otherwise fall back to structured data / the DOM heuristic.
    rank = {"trafilatura": 0, "json-ld": 1, "heuristic": 2}
    substantial = [c for c in candidates if sum(len(p) for p in c[1]) >= 700]
    extractor, paragraphs = min(substantial or candidates, key=lambda c: rank.get(c[0], 9))

    title = (meta.get("og:title") or meta.get("twitter:title") or meta.get("title") or "").strip()
    if not title:
        m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.S | re.I)
        title = unescape(m.group(1)).strip() if m else ""
    if site and title.lower().endswith(site.lower()):
        title = title[: -len(site)].strip(" -|·—")

    byline = (
        meta.get("author")
        or meta.get("article:author")
        or meta.get("twitter:creator")
        or ""
    ).strip()

    # Drop a leading paragraph that is just the headline repeated, plus any
    # near-identical duplicate of the title pulled in by recall mode.
    tnorm = re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()
    if tnorm:
        paragraphs = [
            p
            for p in paragraphs
            if not re.sub(r"[^a-z0-9 ]", "", p.lower()).strip().startswith(tnorm[:70])
        ]
    if not paragraphs:
        return {}

    # Cut at the paywall marker so a teaser is labelled instead of silently
    # looking like a whole story.
    paywalled = False
    for idx, p in enumerate(paragraphs):
        if len(p) < 320 and _PAYWALL_RE.search(p):
            paywalled = True
            paragraphs = paragraphs[:idx]
            break
    if paywalled and not paragraphs:
        return {}

    published = (
        meta.get("article:published_time")
        or meta.get("datepublished")
        or meta.get("pubdate")
        or meta.get("og:published_time")
        or ""
    ).strip()

    return {
        "ok": True,
        "url": final_url,
        "title": title,
        "byline": byline,
        "published": published,
        "site": site,
        "image": meta.get("og:image") or meta.get("twitter:image") or "",
        "excerpt": meta.get("og:description") or meta.get("description") or "",
        "paragraphs": paragraphs,
        "words": sum(len(p.split()) for p in paragraphs),
        "extractor": extractor,
        "paywalled": paywalled,
    }


@app.get("/article/extract")
def extract_article(url: str):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not host:
        raise HTTPException(status_code=400, detail="only http(s) article urls are supported")
    if host == "localhost" or host.endswith(".local") or host.startswith(
        ("127.", "10.", "192.168.", "169.254.")
    ):
        raise HTTPException(status_code=400, detail="host not allowed")

    now = time.time()
    hit = _ARTICLE_CACHE.get(url)
    if hit and (now - hit["ts"]) < _ARTICLE_TTL:
        return hit["data"]

    disk = _disk_get(url)
    if disk:
        _ARTICLE_CACHE[url] = {"ts": float(disk.get("ts") or now), "data": disk["data"]}
        return disk["data"]

    try:
        payload = _extract_article(url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"article fetch failed: {exc}")

    if not payload or not payload.get("paragraphs"):
        raise HTTPException(
            status_code=422,
            detail="no readable body found (paywall, JS-only page, or blocked crawler)",
        )
    if len(_ARTICLE_CACHE) > _ARTICLE_MAX:
        oldest = sorted(_ARTICLE_CACHE, key=lambda k: _ARTICLE_CACHE[k]["ts"])[:50]
        for k in oldest:
            _ARTICLE_CACHE.pop(k, None)
    _ARTICLE_CACHE[url] = {"ts": now, "data": payload}
    _disk_put(url, payload)
    return payload


@app.get("/article/search")
def search_cached_articles(q: str, limit: int = 40):
    """Search the bodies of every article extracted so far (disk cache)."""
    query = (q or "").strip()
    if len(query) < 2:
        return {"query": query, "count": 0, "results": []}
    needle = query.lower()
    limit = max(1, min(int(limit or 40), 100))
    try:
        names = [n for n in os.listdir(_CACHE_DIR) if n.endswith(".json")]
    except Exception:
        names = []
    paths = sorted(
        (os.path.join(_CACHE_DIR, n) for n in names),
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )
    results: list[dict] = []
    seen: set[str] = set()
    for path in paths[:800]:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except Exception:
            continue
        data = rec.get("data") or {}
        if not isinstance(data, dict):
            continue
        url = rec.get("url") or ""
        if not url or url in seen:
            continue
        title = str(data.get("title") or "")
        paras = [str(p) for p in (data.get("paragraphs") or [])]
        body = "\n".join(paras)
        idx = body.lower().find(needle)
        if idx < 0 and needle not in title.lower():
            continue
        seen.add(url)
        if idx >= 0:
            start = max(0, idx - 70)
            end = min(len(body), idx + len(needle) + 130)
            snippet = body[start:end].replace("\n", " ").strip()
            snippet = ("…" if start else "") + snippet + ("…" if end < len(body) else "")
        else:
            snippet = paras[0][:200] if paras else ""
        results.append(
            {
                "url": url,
                "title": title,
                "site": data.get("site") or "",
                "words": data.get("words") or 0,
                "paywalled": bool(data.get("paywalled")),
                "snippet": re.sub(r"\s+", " ", snippet),
                "ts": rec.get("ts") or 0,
            }
        )
        if len(results) >= limit:
            break
    return {"query": query, "count": len(results), "results": results}


# Old dashboard-v2 demo URLs used to live here. Keep bookmarks working.
_DASH_PAGES = {
    "index.html",
    "news.html",
    "finance.html",
    "sports.html",
    "weather.html",
    "world.html",
    "planes.html",
    "customize.html",
}


@app.get("/demos/dash")
@app.get("/demos/dash/")
@app.get("/demos/dash/{page}")
def dash_redirect(page: str = "index.html"):
    target = "/" if page in ("", "index.html") or page not in _DASH_PAGES else "/" + page
    return RedirectResponse(url=target, status_code=307)


# Serve the frontend (index.html) as a real website at "/"
# MUST be registered AFTER all API routes, otherwise it shadows them with 404
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6767)
