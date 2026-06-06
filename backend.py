import json
import os
import re
import socket
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import unescape

import feedparser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

socket.setdefaulttimeout(10)

app = FastAPI(title="Retro News Aggregator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Country values must EXACTLY match world-atlas/countries-110m.json
# `properties.name` strings, because the frontend joins on that string.
RAW_FEEDS = [
    # GLOBAL WIRE SERVICES
    # Removed: Reuters, AP, AFP (broken)

    # BROADCAST NETWORKS
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "http://rss.cnn.com/rss/cnn_topstories.rss"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "http://rss.cnn.com/rss/edition_world.rss"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "https://www.cnbc.com/id/100727362/device/rss/rss.html"},
    {"category": "BROADCAST NETWORKS",     "country": "India",               "url": "http://feeds.feedburner.com/ndtvnews-world-news"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "https://feeds.npr.org/1001/rss.xml"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "https://moxie.foxnews.com/google-publisher/latest.xml"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "https://www.cbsnews.com/latest/rss/main"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "https://feeds.nbcnews.com/nbcnews/public/news"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "https://feeds.abcnews.com/abcnews/topstories"},
    {"category": "BROADCAST NETWORKS",     "country": "United States of America","url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    # Removed: PBS (broken)

    # MAJOR NEWSPAPERS
    {"category": "MAJOR NEWSPAPERS",       "country": "United States of America","url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"},
    {"category": "MAJOR NEWSPAPERS",       "country": "United States of America","url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"},
    {"category": "MAJOR NEWSPAPERS",       "country": "India",               "url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"},
    {"category": "MAJOR NEWSPAPERS",       "country": "United States of America","url": "https://feeds.washingtonpost.com/rss/homepage"},
    {"category": "MAJOR NEWSPAPERS",       "country": "United States of America","url": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"},
    # Removed: USA Today, LA Times, Politico (broken)
    {"category": "MAJOR NEWSPAPERS",       "country": "United States of America","url": "https://nypost.com/feed/"},
    {"category": "MAJOR NEWSPAPERS",       "country": "United States of America","url": "https://time.com/feed/"},

    # UK & EUROPEAN FEEDS
    {"category": "UK & EUROPEAN FEEDS",    "country": "United Kingdom",        "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "United Kingdom",        "url": "https://www.theguardian.com/world/rss"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "United Kingdom",        "url": "https://www.ft.com/rss/world"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "United Kingdom",        "url": "https://www.independent.co.uk/news/world/rss"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "United Kingdom",        "url": "https://www.telegraph.co.uk/rss.xml"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "United Kingdom",        "url": "https://feeds.skynews.com/feeds/rss/world.xml"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "Germany",               "url": "https://rss.dw.com/xml/rss-en-world"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "France",                "url": "https://www.france24.com/en/rss"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "France",                "url": "https://www.euronews.com/rss"},
    {"category": "UK & EUROPEAN FEEDS",    "country": "Germany",               "url": "https://www.spiegel.de/international/index.rss"},
    # Removed: El Pais (broken)

    # GLOBAL ENGLISH FEEDS
    # Removed: CBC, Globe & Mail (broken)
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Canada",               "url": "https://www.cbc.ca/cmlink/rss-topstories"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Canada",               "url": "https://globalnews.ca/feed/"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Brazil",               "url": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Germany",              "url": "http://newsfeed.zeit.de/index"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Germany",              "url": "http://www.tagesschau.de/xml/rss2"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "France",               "url": "https://www.lemonde.fr/rss/une.xml"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Spain",                "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "United States of America","url": "https://news.google.com/rss"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Australia",             "url": "https://www.abc.net.au/news/feed/51120/rss.xml"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Australia",             "url": "https://www.smh.com.au/rss/feed.xml"},
    # Removed: NZ Herald (broken)
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Qatar",                 "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    # Removed: SCMP (broken)
    # Removed: India Times (broken)
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "India",                 "url": "https://www.thehindu.com/feeder/default.rss"},
    # Removed: Nikkei Asia (broken)
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Malaysia",              "url": "https://www.channelnewsasia.com/rssfeeds/8395986"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Saudi Arabia",          "url": "https://www.arabnews.com/rss.xml"},
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "Israel",                "url": "https://www.timesofisrael.com/feed/"},
    # Removed: AllAfrica (broken)
    {"category": "GLOBAL ENGLISH FEEDS",   "country": "South Africa",          "url": "https://mg.co.za/feed/"},

    # TECH & FINANCE FEEDS
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://feeds.bloomberg.com/markets/news.rss"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.investing.com/rss/news.rss"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://seekingalpha.com/market_currents.xml"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.forbes.com/business/feed/"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://fortune.com/feed"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://finance.yahoo.com/news/rssindex"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.forbes.com/most-popular/feed/"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://techcrunch.com/feed/"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.theverge.com/rss/index.xml"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.wired.com/feed/rss"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.cnet.com/rss/news/"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://gizmodo.com/rss"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://news.ycombinator.com/rss"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "http://feeds.mashable.com/Mashable"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "http://rss.slashdot.org/Slashdot/slashdotMain"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.blog.google/rss/"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://thenextweb.com/feed/"},
    {"category": "TECH & FINANCE FEEDS",   "country": "United States of America","url": "https://www.engadget.com/rss.xml"},

]

_seen: set[str] = set()
FEEDS: list[dict] = []
for f in RAW_FEEDS:
    if f["url"] not in _seen:
        _seen.add(f["url"])
        FEEDS.append(f)

PER_FEED_QUOTA = 1
MAX_WORKERS = 40
NEWS_CACHE_TTL = 120.0
_YAHOO_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Broaden regex validation to allow stocks, currencies, commodities, cryptos, bonds, index
# e.g. AAPL, GC=F, CL=F, BTC-USD, ^GSPC, EURUSD=X, 2330.TW, BRK/B
SYMBOL_REGEX = r"^[A-Z0-9^=./-]{1,15}$"

_NEWS_CACHE: dict = {"data": None, "ts": 0.0}


def _clean_summary(raw: str, limit: int = 240) -> str:
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 3].rstrip() + "..."
    return text or "[No summary available]"


def _fetch_one(feed: dict) -> list[dict]:
    country = feed.get("country", "")
    try:
        parsed = feedparser.parse(feed["url"])
        entries = parsed.entries[:PER_FEED_QUOTA] if parsed.entries else []
        if not entries:
            return [{
                "category": feed["category"],
                "country":  country,
                "title":    "[ Feed returned no entries ]",
                "link":     feed["url"],
                "summary": (
                    f"feedparser found 0 items at {feed['url']}. "
                    "The URL may not be a valid RSS endpoint."
                ),
            }]
        out: list[dict] = []
        for entry in entries:
            out.append({
                "category": feed["category"],
                "country":  country,
                "title":    (entry.get("title") or "Untitled").strip(),
                "link":     entry.get("link") or feed["url"],
                "summary":  _clean_summary(
                    entry.get("summary") or entry.get("description") or ""
                ),
            })
        return out
    except Exception as exc:
        return [{
            "category": feed["category"],
            "country":  country,
            "title":    "[ Feed error ]",
            "link":     feed["url"],
            "summary":  f"Could not load feed: {exc}",
        }]


@app.get("/news")
def get_news(limit: int = None):
    now = time.time()
    if _NEWS_CACHE["data"] is not None and (now - _NEWS_CACHE["ts"]) < NEWS_CACHE_TTL:
        data = _NEWS_CACHE["data"]
    else:
        # If limit is requested and cache is empty, only fetch a few sources for speed
        feeds_to_fetch = FEEDS
        if limit is not None and _NEWS_CACHE["data"] is None:
            feeds_to_fetch = FEEDS[:limit * 2]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            results = list(pool.map(_fetch_one, feeds_to_fetch))
        stories: list[dict] = []
        for batch in results:
            stories.extend(batch)
        
        _NEWS_CACHE["data"] = stories
        _NEWS_CACHE["ts"] = now
        data = stories
    
    if limit is not None:
        return data[:limit]
    return data


@app.get("/stocks/search")
def search_stocks(q: str):
    query = q.strip()
    if not query:
        return []
    url = (
        "https://query1.finance.yahoo.com/v1/finance/search?"
        + urllib.parse.urlencode({
            "q": query,
            "quotesCount": 10,
            "newsCount": 0,
            "listsCount": 0,
        })
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
                "symbol":    symbol.upper(),
                "name":      q_.get("shortname") or q_.get("longname") or symbol,
                "quoteType": q_.get("quoteType", "UNKNOWN"),
                "exchange":  q_.get("exchange", "UNKNOWN"),
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

@app.get("/stocks/{symbol}")

def get_stocks(symbol: str, range: str = "1y", interval: str = "1d"):
    sym = symbol.strip().upper()
    if not re.match(SYMBOL_REGEX, sym):
        raise HTTPException(status_code=400, detail="Invalid symbol format")

    valid_ranges = {"1d", "5d", "1mo", "3mo", "1y", "max"}
    if range not in valid_ranges:
        range = "1y"

    # ... (existing stock range logic)
    intervals = {
        "1d": "5m",
        "5d": "15m",
        "1mo": "1h",
        "3mo": "1d",
        "1y": "1d",
        "max": "1d",
    }
    interval = intervals[range]
    # ...


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
        raise HTTPException(status_code=502, detail="yahoo returned no result")
    r = result[0]
    m = r.get("meta") or {}
    q = ((r.get("indicators") or {}).get("quote") or [{}])[0]
    timestamps = r.get("timestamp") or []
    closes_raw = q.get("close") or []
    opens_raw  = q.get("open") or []
    highs_raw  = q.get("high") or []
    lows_raw   = q.get("low") or []
    vols_raw   = q.get("volume") or []

    last = m.get("regularMarketPrice")
    prev = m.get("chartPreviousClose")
    change = (last - prev) if (last is not None and prev is not None) else None
    change_pct = (
        (change / prev * 100.0) if (change is not None and prev not in (None, 0)) else None
    )

    last_idx = -1
    while last_idx >= -len(closes_raw) and closes_raw[last_idx] is None:
        last_idx -= 1

    def safe(arr, idx):
        a = len(arr)
        if not (-a <= idx < a):
            return None
        v = arr[idx]
        return v if v is not None else None

    day_open  = safe(opens_raw,  last_idx)
    day_high  = safe(highs_raw,  last_idx)
    day_low   = safe(lows_raw,   last_idx)
    day_vol   = safe(vols_raw,   last_idx)

    closes_52w = [c for c in closes_raw if c is not None]
    highs_52w  = [h for h in highs_raw  if h is not None]
    lows_52w   = [l for l in lows_raw   if l is not None]

    # Dynamic date/time formatting based on range
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
            "date":  time.strftime(fmt, time.gmtime(local_ts)),
            "close": round(float(c), 4),
            "volume": safe(vols_raw, i),
        })

    # ... (existing logic up to the return statement)
    
    # Fetch additional summary metrics
    summary_url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}?modules=defaultKeyStatistics,financialData"
    summary_req = urllib.request.Request(summary_url, headers={"User-Agent": _YAHOO_UA})
    summary_data = {}
    try:
        summary_body = urllib.request.urlopen(summary_req, timeout=10).read()
        summary_json = json.loads(summary_body)
        res_sum = summary_json.get("quoteSummary", {}).get("result", [{}])[0]
        summary_data = res_sum
    except:
        pass

    def get_sum(module, key):
        return summary_data.get(module, {}).get(key, {}).get("raw", "—")

    return {
        "symbol":         sym,
        "name":           m.get("longName") or m.get("shortName") or sym,
        "exchange":       m.get("exchangeName") or m.get("fullExchangeName"),
        "currency":       m.get("currency"),
        "last":           last,
        "previousClose":  prev,
        "change":         (round(change, 4) if change is not None else None),
        "changePct":      (round(change_pct, 3) if change_pct is not None else None),
        "dayOpen":        day_open,
        "dayHigh":        day_high,
        "dayLow":         day_low,
        "volume":         day_vol,
        "fiftyTwoHigh":   m.get("fiftyTwoWeekHigh") or (max(highs_52w) if highs_52w else None),
        "fiftyTwoLow":    m.get("fiftyTwoWeekLow")  or (min(lows_52w)  if lows_52w  else None),
        "history":        history,
        "metrics": {
            "pe": get_sum("defaultKeyStatistics", "trailingPE"),
            "marketCap": get_sum("defaultKeyStatistics", "marketCap"),
            "dividend": get_sum("summaryDetail", "dividendYield"),
        }
    }



# Serve the frontend (index.html) as a real website at "/"
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=6767)
