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

# Buscar sin provincia para obtener más resultados
url = 'https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=React'
r = session.get(url, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

# Solo cards reales (con ij-OfferCardContent dentro)
cards = [c for c in soup.find_all('li', class_='ij-OfferList-offerCardItem')
         if c.find('div', class_='ij-OfferCardContent')]

print(f"Ofertas reales encontradas: {len(cards)}")

for i, card in enumerate(cards[:5]):
    titulo = card.find('span', class_='ij-OfferCardContent-description-title-link')
    empresa = card.find('h3', class_='ij-OfferCardContent-description-subtitle')
    link = card.find('a', class_='ij-OfferCardContent-description-link')
    salario = card.find('span', class_='ij-OfferCardContent-description-salary-info')
    items = card.find_all('li', class_='ij-OfferCardContent-description-list-item')
    hidden_items = card.find_all('li', class_='ij-OfferCardContent-description-list-item--hideOnMobile')

    print(f"\n--- Oferta {i+1} ---")
    print(f"  Titulo:  {titulo.get_text(strip=True) if titulo else 'N/A'}")
    print(f"  Empresa: {empresa.get_text(strip=True) if empresa else 'N/A'}")
    print(f"  URL:     {link.get('href', 'N/A') if link else 'N/A'}")
    print(f"  Salario: {salario.get_text(strip=True) if salario else 'N/A'}")
    print(f"  Items:   {[i.get_text(strip=True) for i in items]}")
    print(f"  Hidden:  {[i.get_text(strip=True) for i in hidden_items]}")
