import requests
from bs4 import BeautifulSoup
import hashlib
from typing import List, Dict

# Mapa de ciudad → provinceId (códigos INE de España)
PROVINCE_IDS = {
    'alava': 1, 'albacete': 2, 'alicante': 3, 'almeria': 4, 'avila': 5,
    'badajoz': 6, 'baleares': 7, 'barcelona': 8, 'burgos': 9, 'caceres': 10,
    'cadiz': 11, 'castellon': 12, 'ciudadreal': 13, 'cordoba': 14, 'coruna': 15,
    'cuenca': 16, 'girona': 17, 'granada': 18, 'guadalajara': 19, 'guipuzcoa': 20,
    'huelva': 21, 'huesca': 22, 'jaen': 23, 'leon': 24, 'lleida': 25,
    'rioja': 26, 'lugo': 27, 'madrid': 28, 'malaga': 29, 'murcia': 30,
    'navarra': 31, 'ourense': 32, 'asturias': 33, 'palencia': 34, 'laspalmas': 35,
    'pontevedra': 36, 'salamanca': 37, 'tenerife': 38, 'cantabria': 39, 'segovia': 40,
    'sevilla': 41, 'soria': 42, 'tarragona': 43, 'teruel': 44, 'toledo': 45,
    'valencia': 46, 'valladolid': 47, 'vizcaya': 48, 'zamora': 49, 'zaragoza': 50,
}

def _normalize(text: str) -> str:
    import unicodedata
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

def build_infojobs_url(user_config: Dict) -> str:
    """Construye la URL de búsqueda de InfoJobs"""
    stack = user_config.get('stack', 'React')
    ubicacion = user_config.get('ubicacion', 'Málaga')

    keyword = [s.strip() for s in stack.split(',')][0]
    ciudad_norm = _normalize(ubicacion.split(',')[0].split()[0])
    province_id = PROVINCE_IDS.get(ciudad_norm, '')

    base = f"https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword={keyword}"
    if province_id:
        base += f"&provinceIds={province_id}"
    return base

def fetch_infojobs(user_config: Dict) -> List[Dict]:
    """Obtiene ofertas de InfoJobs scrapeando HTML"""
    url = build_infojobs_url(user_config)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        ofertas = []

        items = soup.find_all('li', class_='ij-OfferList-offerCardItem')

        for item in items:
            try:
                titulo_elem = item.find('span', class_='ij-OfferCardContent-description-title-link')
                link_elem = item.find('a', class_='ij-OfferCardContent-description-link')
                empresa_elem = item.find('h3', class_='ij-OfferCardContent-description-subtitle')

                if not titulo_elem or not link_elem:
                    continue

                titulo = titulo_elem.get_text(strip=True)
                empresa_a = empresa_elem.find('a') if empresa_elem else None
                empresa = empresa_a.get_text(strip=True) if empresa_a else 'Desconocida'
                url_oferta = link_elem.get('href', '')
                if url_oferta.startswith('//'):
                    url_oferta = 'https:' + url_oferta

                offer_id = hashlib.md5(f"infojobs_{url_oferta}".encode()).hexdigest()[:12]

                oferta = {
                    'id': offer_id,
                    'titulo': titulo,
                    'empresa': empresa,
                    'url': url_oferta,
                    'descripcion': titulo,
                    'fuente': 'infojobs',
                    'fecha_publicacion': '',
                }
                ofertas.append(oferta)

            except Exception as e:
                print(f"[Error parseando oferta]: {e}")
                continue

        print(f"[InfoJobs] {len(ofertas)} ofertas encontradas en: {url}")
        return ofertas

    except Exception as e:
        print(f"[ERROR] InfoJobs: {e}")
        return []