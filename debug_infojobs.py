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

# Buscar cualquier elemento que contenga título de oferta
print("=== Buscando 'oferta' en clases de elementos ===")
for tag in soup.find_all(True):
    cls = ' '.join(tag.get('class', []))
    if 'offer' in cls.lower() or 'ofert' in cls.lower() or 'job' in cls.lower():
        txt = tag.get_text(strip=True)[:80]
        print(f"  <{tag.name} class='{cls}'> {txt}")

print("\n=== Buscando <article> o <section> con contenido de oferta ===")
for tag in soup.find_all(['article', 'section', 'div']):
    cls = ' '.join(tag.get('class', []))
    if any(x in cls for x in ['card', 'Card', 'result', 'Result', 'item', 'Item']):
        txt = tag.get_text(strip=True)[:100]
        if txt:
            print(f"  <{tag.name} class='{cls}'> {txt[:80]}")
