import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Referer': 'https://www.infojobs.net/',
    'Connection': 'keep-alive',
})

session.get('https://www.infojobs.net/', timeout=15)

url = 'https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=React&provinceIds=29'
r = session.get(url, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

cards = soup.find_all('li', class_='ij-OfferList-offerCardItem')
print(f"Cards encontradas: {len(cards)}")

if cards:
    print("\n--- HTML PRIMERA CARD ---")
    print(cards[0].prettify()[:3000])
