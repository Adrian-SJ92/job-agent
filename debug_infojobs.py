import feedparser
import requests

urls = [
    'https://www.infojobs.net/rss/search?q=React&city=malaga',
    'https://www.infojobs.net/rss/search?q=React&city=m%C3%A1laga',
    'https://www.infojobs.net/rss/search?q=React',
    'https://www.infojobs.net/rss/search?q=programador',
    'https://www.infojobs.net/rss/ofertas.xhtml?segmentId=0&q=React',
]

for url in urls:
    feed = feedparser.parse(url)
    print(f"\n{url}")
    print(f"  Entries: {len(feed.entries)} | Status: {feed.get('status', '?')} | bozo: {feed.get('bozo', '?')}")
    if feed.entries:
        print(f"  Primera: {feed.entries[0].get('title', 'N/A')}")
    elif feed.feed:
        print(f"  Feed title: {feed.feed.get('title', 'N/A')}")

# Probar también con requests directo para ver qué devuelve
print("\n--- RAW RSS con requests ---")
r = requests.get('https://www.infojobs.net/rss/search?q=React', timeout=10)
print(f"Status: {r.status_code}")
print(r.text[:500])
