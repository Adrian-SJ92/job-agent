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

urls_a_probar = [
    'https://www.infojobs.net/ofertas-trabajo/malaga/react',
    'https://www.infojobs.net/ofertas-trabajo/malaga/react?page=1',
    'https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=React&provinceIds=29',
    'https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=React&provinceIds=29&page=1',
]

for url in urls_a_probar:
    r = session.get(url, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    all_cards = soup.find_all('li', class_='ij-OfferList-offerCardItem')
    real_cards = [c for c in all_cards if 'sui-PrimitiveLinkBox' in ' '.join(c.get('class', []))]
    print(f"\nURL: {url}")
    print(f"  Total cards: {len(all_cards)} | Reales: {len(real_cards)}")
    if real_cards:
        first = real_cards[0]
        titulo = first.find('span', class_='ij-OfferCardContent-description-title-link')
        link = first.find('a', class_='ij-OfferCardContent-description-link')
        salario = first.find('span', class_='ij-OfferCardContent-description-salary-info')
        print(f"  Titulo: {titulo.get_text(strip=True)[:60] if titulo else 'N/A'}")
        print(f"  URL:    {link.get('href', 'N/A') if link else 'N/A'}")
        print(f"  Salario:{salario.get_text(strip=True) if salario else 'N/A'}")
