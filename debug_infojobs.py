import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.infojobs.net/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
})

# Primero cargar la home para obtener cookies de sesión
print("Cargando home...")
session.get('https://www.infojobs.net/', timeout=15)

print("Buscando ofertas React en Málaga...")
url = 'https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=React&provinceIds=29'
r = session.get(url, timeout=15)
print(f"Status: {r.status_code} | HTML: {len(r.text)} chars")

if 'captcha' in r.text.lower():
    print("CAPTCHA — bloqueado también con requests")
else:
    print("SIN CAPTCHA — analizando estructura...")
    soup = BeautifulSoup(r.text, 'html.parser')
    # Buscar cualquier lista de ofertas
    for li in soup.find_all('li')[:15]:
        cls = li.get('class', [])
        if cls:
            print(f"  <li class='{' '.join(cls)}'>")

print("\n--- PRIMEROS 2000 CHARS ---")
print(r.text[:2000])
