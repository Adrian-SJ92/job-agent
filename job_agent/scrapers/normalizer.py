from typing import List, Dict
from datetime import datetime

def normalize_oferta(oferta: Dict) -> Dict:
    """
    Normaliza una oferta de cualquier fuente al formato estándar.
    
    Formato estándar:
    {
        'id': str (único),
        'titulo': str,
        'empresa': str,
        'url': str,
        'descripcion': str,
        'fuente': str (infojobs, linkedin, etc),
        'fecha_publicacion': str
    }
    """
    return {
        'id': oferta.get('id', ''),
        'titulo': oferta.get('titulo', '').strip(),
        'empresa': oferta.get('empresa', 'Desconocida').strip(),
        'url': oferta.get('url', ''),
        'descripcion': oferta.get('descripcion', '').strip(),
        'fuente': oferta.get('fuente', 'desconocida'),
        'fecha_publicacion': oferta.get('fecha_publicacion', datetime.now().isoformat())
    }

def deduplicate_ofertas(ofertas: List[Dict]) -> List[Dict]:
    """
    Elimina ofertas duplicadas usando el ID como clave.
    Mantiene la primera ocurrencia.
    """
    seen = set()
    unique = []
    
    for oferta in ofertas:
        offer_id = oferta.get('id')
        if offer_id not in seen:
            seen.add(offer_id)
            unique.append(oferta)
    
    print(f"[Deduplicación] {len(ofertas)} → {len(unique)} ofertas únicas")
    return unique

def merge_sources(infojobs_ofertas: List[Dict], linkedin_ofertas: List[Dict]) -> List[Dict]:
    """
    Fusiona ofertas de múltiples fuentes y las normaliza.
    """
    all_ofertas = []
    
    # Normalizar y fusionar
    for oferta in infojobs_ofertas + linkedin_ofertas:
        normalized = normalize_oferta(oferta)
        all_ofertas.append(normalized)
    
    # Deduplicar
    unique_ofertas = deduplicate_ofertas(all_ofertas)
    
    return unique_ofertas