import feedparser
import urllib.request

NEW_FEEDS_TO_TEST = [
    ("CBC Canada", "https://www.cbc.ca/cmlink/rss-topstories", "Canada"),
    ("CTV News Canada", "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009", "Canada"),
    ("Global News Canada", "https://globalnews.ca/feed/", "Canada"),
    ("Folha de S.Paulo Brazil", "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml", "Brazil"),
    ("UOL Brazil", "http://rss.home.uol.com.br/index.xml", "Brazil"),
    ("Zeit Online Germany", "http://newsfeed.zeit.de/index", "Germany"),
    ("Tagesschau Germany", "http://www.tagesschau.de/xml/rss2", "Germany"),
    ("Le Monde France", "https://www.lemonde.fr/rss/une.xml", "France"),
    ("El Pais Spain", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "Spain"),
    ("El Mundo Spain", "https://www.elmundo.es/rss/portada", "Spain"),
    ("ANSA Italy", "https://www.ansa.it/rss/", "Italy"),
    ("NHK World Japan", "https://www3.nhk.or.jp/nhkworld/en/news/rss/", "Japan"),
]

def test_feed(name, url, country):
    print(f"Testing {name} ({url})...", end=" ")
    try:
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
    for name, url, country in NEW_FEEDS_TO_TEST:
        success = test_feed(name, url, country)
        if success:
            results.append({"category": "GLOBAL", "country": country, "url": url, "name": name})
    
    print("\nVerified feeds to add:")
    for r in results:
        print(f"{{'category': '{r['category']}', 'country': '{r['country']}', 'url': '{r['url']}'}},")
