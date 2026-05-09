import requests
import hashlib
import base64
import unicodedata
from typing import List, Dict

API_URL = "https://api.infojobs.net/api/7/offer"

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


def fetch_infojobs(user_config: Dict) -> List[Dict]:
    client_id = user_config.get('INFOJOBS_CLIENT_ID', '')
    client_secret = user_config.get('INFOJOBS_CLIENT_SECRET', '')
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    keyword = user_config.get('stack', 'React').split(',')[0].strip()
    ciudad = _normalize(user_config.get('ubicacion', 'Málaga').split(',')[0].split()[0])
    province_id = PROVINCE_IDS.get(ciudad, '')

    params = {'q': keyword, 'maxResults': 20, 'page': 1}
    if province_id:
        params['province'] = province_id

    headers = {'Authorization': f'Basic {credentials}', 'Accept': 'application/json'}

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        ofertas = []
        for item in data.get('items', []):
            salary_min = item.get('salaryMin', {}).get('id', 0)
            salary_max = item.get('salaryMax', {}).get('id', 0)
            contract = item.get('contractType', {}).get('value', '')
            telework = item.get('teleworking', {}).get('value', '')

            descripcion = f"{item.get('requirementMin', '')} | {contract} | {telework} | Salario: {salary_min}-{salary_max}€"
            url_oferta = item.get('link', '')
            offer_id = hashlib.md5(f"infojobs_{url_oferta}".encode()).hexdigest()[:12]

            ofertas.append({
                'id': offer_id,
                'titulo': item.get('title', ''),
                'empresa': item.get('author', {}).get('name', 'Desconocida'),
                'url': url_oferta,
                'descripcion': descripcion,
                'fuente': 'infojobs',
                'fecha_publicacion': item.get('published', ''),
            })

        print(f"[InfoJobs API] {len(ofertas)} ofertas encontradas")
        return ofertas

    except Exception as e:
        print(f"[ERROR] InfoJobs API: {e}")
        return []
