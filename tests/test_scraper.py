from job_agent.db.schema import get_user_by_username
from job_agent.scrapers.infojobs import fetch_infojobs

user = get_user_by_username("adriansj92")
print(f"Usuario: {user['username']}")
print(f"Criterios: {user['sueldo_min']}€, {user['stack']}, {user['ubicacion']}")

print("\n[*] Scrapeando InfoJobs...")
ofertas = fetch_infojobs(user)

print(f"\n[*] Ofertas encontradas: {len(ofertas)}")
for i, oferta in enumerate(ofertas[:3]):
    print(f"  {i+1}. {oferta['titulo']} - {oferta['empresa']}")