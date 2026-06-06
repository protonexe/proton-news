import feedparser
import urllib.request

FEEDS_TO_TEST = [
    ("CNN World", "http://rss.cnn.com/rss/edition_world.rss", "United States of America"),
    ("CNBC International", "https://www.cnbc.com/id/100727362/device/rss/rss.html", "United States of America"),
    ("NDTV World", "http://feeds.feedburner.com/ndtvnews-world-news", "India"),
    ("NYT World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "United States of America"),
    ("Google News", "https://news.google.com/rss", "United States of America"),
    ("Wash Post World", "http://feeds.washingtonpost.com/rss/world", "United States of America"),
    ("Reddit World News", "https://www.reddit.com/r/worldnews/.rss", "United States of America"),
    ("Times of India World", "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", "India"),
    ("Yahoo News", "https://www.yahoo.com/news/rss", "United States of America"),
    ("Investing.com", "https://www.investing.com/rss/news.rss", "United States of America"),
    ("Seeking Alpha", "https://seekingalpha.com/market_currents.xml", "United States of America"),
    ("Forbes Business", "https://www.forbes.com/business/feed/", "United States of America"),
    ("Fortune", "https://fortune.com/feed", "United States of America"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex", "United States of America"),
    ("CNET News", "https://www.cnet.com/rss/news/", "United States of America"),
    ("Gizmodo", "https://gizmodo.com/rss", "United States of America"),
    ("Hacker News", "https://news.ycombinator.com/rss", "United States of America"),
    ("Mashable", "http://feeds.mashable.com/Mashable", "United States of America"),
    ("Slashdot", "http://rss.slashdot.org/Slashdot/slashdotMain", "United States of America"),
    ("Google Blog", "https://www.blog.google/rss/", "United States of America"),
    ("The Next Web", "https://thenextweb.com/feed/", "United States of America"),
    ("Engadget", "https://www.engadget.com/rss.xml", "United States of America"),
]

def test_feed(name, url, country):
    print(f"Testing {name} ({url})...", end=" ")
    try:
        # Use a browser User-Agent to avoid 403/429
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            parsed = feedparser.parse(content)
            if parsed.entries:
                print("SUCCESS")
                return True
            else:
                print("EMPTY")
                return False
    except Exception as e:
        print(f"FAILED ({e})")
        return False

if __name__ == "__main__":
    results = []
    for name, url, country in FEEDS_TO_TEST:
        success = test_feed(name, url, country)
        if success:
            results.append({"category": "GLOBAL", "country": country, "url": url, "name": name})
    
    print("\nVerified feeds to add:")
    for r in results:
        print(f"{{'category': '{r['category']}', 'country': '{r['country']}', 'url': '{r['url']}'}},")
