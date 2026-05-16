from job_agent.db.schema import get_user_by_username
from job_agent.config.config_manager import load_user_config
from job_agent.scrapers.gmail import fetch_linkedin_alerts

USERNAME = "adriansj92"
user = get_user_by_username(USERNAME)
env_config = load_user_config(USERNAME)
user_config = {**user, **env_config}

print(f"Usuario: {user_config['username']}")
print(f"Criterios: {user_config['sueldo_min']}€, {user_config['stack']}, {user_config['ubicacion']}")

print("\n[*] Scrapeando alertas de LinkedIn via Gmail...")
ofertas = fetch_linkedin_alerts(user_config)

print(f"\n[*] Ofertas encontradas: {len(ofertas)}")
for i, oferta in enumerate(ofertas[:5]):
    print(f"  {i+1}. {oferta['titulo']}")
    print(f"     URL: {oferta['url'] or '(sin URL)'}")
    print(f"     Fecha: {oferta['fecha_publicacion']}")
