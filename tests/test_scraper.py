from job_agent.db.schema import get_user_by_username
from job_agent.scrapers.infojobs import build_infojobs_url

user = get_user_by_username("adriansj92")
url = build_infojobs_url(user)
print(f"URL generada: {url}")

# Ahora intenta parsear el RSS manualmente
import feedparser
feed = feedparser.parse(url)
print(f"Entries en feed: {len(feed.entries)}")
for i, entry in enumerate(feed.entries[:3]):
    print(f"  {i+1}. {entry.get('title', 'Sin título')}")