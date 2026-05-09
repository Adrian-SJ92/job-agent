import requests
from bs4 import BeautifulSoup
import hashlib
from typing import List, Dict
import unicodedata

def clean_text(text):
    """Elimina acentos y caracteres especiales"""
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

def build_infojobs_url(user_config: Dict) -> str:
    """Construye la URL de búsqueda de InfoJobs"""
    stack = user_config.get('stack', 'React')
    ubicacion = user_config.get('ubicacion', 'Málaga')
    
    # Tomar el primer stack
    stack_list = [s.strip() for s in stack.split(',')]
    keyword = stack_list[0].lower()
    
    # Limpiar ubicación
    ciudad = clean_text(ubicacion.split(',')[0].split()[0])
    
    # Construir URL
    url = f"https://www.infojobs.net/busquedas/{keyword}/en-{ciudad}.html"
    return url

def fetch_infojobs(user_config: Dict) -> List[Dict]:
    """Obtiene ofertas de InfoJobs scrapeando HTML"""
    url = build_infojobs_url(user_config)
    
    try:
        # Headers para evitar bloqueos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        ofertas = []
        
        # Buscar elementos con clase de oferta (ajusta el selector según InfoJobs)
        articles = soup.find_all('article', class_='o-anchorJobOffer')
        
        for article in articles:
            try:
                # Extraer datos
                titulo_elem = article.find('h2', class_='o-anchorJobOffer__title')
                empresa_elem = article.find('span', class_='o-anchorJobOffer__company')
                link_elem = article.find('a', class_='o-anchorJobOffer__link')
                
                if not titulo_elem or not link_elem:
                    continue
                
                titulo = titulo_elem.get_text(strip=True)
                empresa = empresa_elem.get_text(strip=True) if empresa_elem else 'Desconocida'
                url_oferta = link_elem.get('href', '')
                
                # Generar ID único
                offer_id = hashlib.md5(f"infojobs_{url_oferta}".encode()).hexdigest()[:12]
                
                oferta = {
                    'id': offer_id,
                    'titulo': titulo,
                    'empresa': empresa,
                    'url': url_oferta,
                    'descripcion': titulo,  # InfoJobs requiere click para ver descripción
                    'fuente': 'infojobs',
                    'fecha_publicacion': ''
                }
                ofertas.append(oferta)
                
            except Exception as e:
                print(f"[Error parseando oferta]: {e}")
                continue
        
        print(f"[InfoJobs] {len(ofertas)} ofertas encontradas")
        return ofertas
        
    except Exception as e:
        print(f"[ERROR] InfoJobs: {e}")
        return []