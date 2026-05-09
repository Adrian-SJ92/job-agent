import feedparser
import hashlib
from typing import List, Dict

def build_infojobs_url(user_config: Dict) -> str:
    """Construye la URL del RSS de InfoJobs según criterios del usuario"""
    stack = user_config.get('stack', 'React')
    ubicacion = user_config.get('ubicacion', 'Málaga')
    
    # Mapeo de stacks a palabras clave de InfoJobs
    stack_keywords = {
        'React': 'react',
        'Node': 'node.js',
        'Python': 'python',
        'Vue': 'vue',
        'Angular': 'angular',
        'JavaScript': 'javascript'
    }
    
    # Tomar el primer stack del usuario
    stack_list = [s.strip() for s in stack.split(',')]
    keyword = stack_keywords.get(stack_list[0], stack_list[0].lower())
    
    # Limpiar ubicación: solo la primera palabra
    ciudad = ubicacion.split(',')[0].split()[0].lower()
    
    # Construir URL
    url = f"https://www.infojobs.net/rss/search?q={keyword}&city={ciudad}&experience=junior"
    return url


def fetch_infojobs(user_config: Dict) -> List[Dict]:
    """Obtiene ofertas de InfoJobs"""
    url = build_infojobs_url(user_config)
    
    try:
        feed = feedparser.parse(url)
        ofertas = []
        
        for entry in feed.entries:
            # Generar ID único
            offer_id = hashlib.md5(f"infojobs_{entry.get('id', entry.get('title', ''))}".encode()).hexdigest()[:12]
            
            oferta = {
                'id': offer_id,
                'titulo': entry.get('title', ''),
                'empresa': entry.get('author', 'Desconocida'),
                'url': entry.get('link', ''),
                'descripcion': entry.get('summary', ''),
                'fuente': 'infojobs',
                'fecha_publicacion': entry.get('published', '')
            }
            ofertas.append(oferta)
        
        print(f"[InfoJobs] {len(ofertas)} ofertas encontradas")
        return ofertas
        
    except Exception as e:
        print(f"[ERROR] InfoJobs: {e}")
        return []