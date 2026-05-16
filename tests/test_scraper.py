from job_agent.db.schema import get_user_by_username
from job_agent.scrapers.gmail import fetch_linkedin_alerts

user = get_user_by_username("adriansj92")
print(f"Usuario: {user['username']}")
print(f"Criterios: {user['sueldo_min']}€, {user['stack']}, {user['ubicacion']}")

print("\n[*] Scrapeando alertas de LinkedIn via Gmail...")
ofertas = fetch_linkedin_alerts(user)

print(f"\n[*] Ofertas encontradas: {len(ofertas)}")
for i, oferta in enumerate(ofertas[:5]):
    print(f"  {i+1}. {oferta['titulo']}")
    print(f"     URL: {oferta['url'] or '(sin URL)'}")
    print(f"     Fecha: {oferta['fecha_publicacion']}")
