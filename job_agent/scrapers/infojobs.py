import hashlib
import time
import unicodedata
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.infojobs.net/jobsearch/search-results/list.xhtml"

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
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()


def _get_driver(user_config: Dict) -> webdriver.Chrome:
    import platform

    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('user-agent=Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36')

    chrome_bin = user_config.get('CHROME_BINARY', '')
    chromedriver_bin = user_config.get('CHROMEDRIVER_BINARY', '')

    # En ARM (Raspberry Pi) el Selenium Manager no soporta ARM.
    # webdriver-manager tampoco: descarga binarios x86-64.
    # Usar el chromedriver del sistema: sudo apt install chromium-driver
    if platform.machine() in ('aarch64', 'armv7l', 'armv8l'):
        chrome_bin = chrome_bin or '/usr/bin/chromium'
        chromedriver_bin = chromedriver_bin or '/usr/bin/chromedriver'

    if chrome_bin:
        opts.binary_location = chrome_bin

    service = Service(chromedriver_bin) if chromedriver_bin else Service()
    return webdriver.Chrome(service=service, options=opts)


def _scrape_search_results(driver, keyword: str, province_id) -> List[dict]:
    """Fase 1: resultados de búsqueda → lista de (título, url, empresa)."""
    url = f"{SEARCH_URL}?keyword={keyword}"
    if province_id:
        url += f"&provinceIds={province_id}"
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'li.ij-OfferList-offerCardItem'))
        )
    except TimeoutException:
        print("[InfoJobs] Timeout esperando resultados")
        return []
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = []
    for item in soup.find_all('li', class_='ij-OfferList-offerCardItem'):
        link = item.find('a', class_='ij-OfferCardContent-description-title-link')
        empresa_elem = item.find('h3', class_='ij-OfferCardContent-description-subtitle')
        if not link:
            continue
        href = link.get('href', '')
        if href.startswith('//'):
            href = 'https:' + href
        results.append({
            'titulo': link.get_text(strip=True),
            'url': href,
            'empresa': empresa_elem.get_text(strip=True) if empresa_elem else 'Desconocida',
        })
    return results


def _scrape_offer_detail(driver, url: str) -> dict:
    """Fase 2: detalle de oferta → salario, contrato, teletrabajo, requisitos."""
    driver.get(url)
    time.sleep(1.5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    salario, contrato = '', ''
    for div in soup.find_all('div', class_='col-child'):
        txt = div.get_text(' ', strip=True)
        if 'Salario' in txt:
            salario = txt
        if 'Jornada' in txt or 'Teletrabajo' in txt or 'Contrato' in txt:
            contrato += f" {txt}"
    req_div = soup.find('div', class_='ij-OfferDetail-body')
    requisitos = req_div.get_text(' ', strip=True)[:400] if req_div else ''
    return {'salario': salario.strip(), 'contrato': contrato.strip(), 'requisitos': requisitos}


def fetch_infojobs(user_config: Dict) -> List[Dict]:
    keyword = user_config.get('stack', 'React').split(',')[0].strip()
    ciudad = _normalize(user_config.get('ubicacion', 'Málaga').split(',')[0].split()[0])
    province_id = PROVINCE_IDS.get(ciudad, '')

    driver = _get_driver(user_config)
    ofertas = []
    try:
        ofertas_base = _scrape_search_results(driver, keyword, province_id)
        for base in ofertas_base[:15]:
            detail = _scrape_offer_detail(driver, base['url'])
            offer_id = hashlib.md5(f"infojobs_{base['url']}".encode()).hexdigest()[:12]
            descripcion = f"{detail['requisitos']} | {detail['contrato']} | Salario: {detail['salario']}"
            ofertas.append({
                'id': offer_id,
                'titulo': base['titulo'],
                'empresa': base['empresa'],
                'url': base['url'],
                'descripcion': descripcion,
                'fuente': 'infojobs',
                'fecha_publicacion': '',
            })
            time.sleep(1)
    except Exception as e:
        print(f"[ERROR] InfoJobs Selenium: {e}")
    finally:
        driver.quit()

    print(f"[InfoJobs Selenium] {len(ofertas)} ofertas encontradas")
    return ofertas
