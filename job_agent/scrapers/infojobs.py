import feedparser
import hashlib
import time
import unicodedata
import requests
from typing import List, Dict
from bs4 import BeautifulSoup

RSS_URL = "https://www.infojobs.net/rss/search"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Referer': 'https://www.infojobs.net/',
    'Connection': 'keep-alive',
}


def _normalize(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()


def _build_rss_url(user_config: Dict) -> str:
    stack = user_config.get('stack') or user_config.get('STACK', 'React')
    ubicacion = user_config.get('ubicacion') or user_config.get('UBICACION', 'Málaga')
    keyword = stack.split(',')[0].strip()
    ciudad = _normalize(ubicacion.split(',')[0].split()[0])
    return f"{RSS_URL}?q={keyword}&city={ciudad}"


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get('https://www.infojobs.net/', timeout=10)
    except Exception:
        pass
    return session


def _scrape_detail(session: requests.Session, url: str) -> dict:
    """Visita la página de detalle y extrae salario, contrato y teletrabajo."""
    result = {'salario': '', 'contrato': '', 'teletrabajo': ''}
    try:
        r = session.get(url, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup.find_all(['span', 'li', 'div', 'p']):
            txt = tag.get_text(' ', strip=True)
            if len(txt) > 150:
                continue
            if 'Salario' in txt and not result['salario']:
                result['salario'] = txt
            if ('Contrato' in txt or 'Jornada' in txt) and not result['contrato']:
                result['contrato'] = txt
            if ('Teletrabajo' in txt or 'Remoto' in txt or 'Híbrido' in txt) and not result['teletrabajo']:
                result['teletrabajo'] = txt
    except Exception as e:
        print(f"  [!] Detalle no disponible: {e}")
    return result


def fetch_infojobs(user_config: Dict) -> List[Dict]:
    rss_url = _build_rss_url(user_config)
    print(f"[InfoJobs] RSS: {rss_url}")

    feed = feedparser.parse(rss_url)
    if not feed.entries:
        print("[InfoJobs] RSS sin resultados")
        return []

    session = _get_session()
    ofertas = []

    for entry in feed.entries[:20]:
        url = entry.get('link', '')
        if not url:
            continue

        detail = _scrape_detail(session, url)
        time.sleep(1)

        offer_id = hashlib.md5(f"infojobs_{url}".encode()).hexdigest()[:12]
        descripcion = entry.get('summary', '')
        extra = ' | '.join(filter(None, [detail['contrato'], detail['teletrabajo'], detail['salario']]))
        if extra:
            descripcion = f"{descripcion} | {extra}"

        ofertas.append({
            'id': offer_id,
            'titulo': entry.get('title', ''),
            'empresa': entry.get('author', 'Desconocida'),
            'url': url,
            'descripcion': descripcion,
            'fuente': 'infojobs',
            'fecha_publicacion': entry.get('published', ''),
        })

    print(f"[InfoJobs] {len(ofertas)} ofertas encontradas")
    return ofertas
