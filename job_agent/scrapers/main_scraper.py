import sys
import os
import argparse
from dotenv import load_dotenv
from .infojobs import fetch_infojobs
from .gmail import fetch_linkedin_alerts
from .normalizer import merge_sources
from job_agent.db.schema import get_user_by_username, save_oferta
from job_agent.classifier import classify_oferta
from job_agent.notifier import notify_ofertas


def _load_user_env(username: str):
    """Carga el .env del usuario al inicio para que todos los módulos lo vean."""
    env_path = os.path.join('config', f'{username}.env')
    if not os.path.exists(env_path):
        candidates = [f for f in os.listdir('config') if f.endswith('.env') and not f.endswith('.example')]
        env_path = os.path.join('config', candidates[0]) if candidates else env_path
    load_dotenv(env_path, override=True)
    print(f"[Config] Cargado {env_path}")

def run_scraper_for_user(username: str):
    """
    Ejecuta el scraper completo para un usuario.
    1. Obtiene credenciales del usuario
    2. Scrappea InfoJobs + LinkedIn
    3. Clasifica con Claude
    4. Guarda en BD
    """

    # Paso 1: Cargar .env y obtener usuario de BD
    _load_user_env(username)
    user = get_user_by_username(username)
    if not user:
        print(f"[ERROR] Usuario '{username}' no encontrado")
        return

    user_id = user['id']
    print(f"\n[*] Iniciando scraper para: {username}")
    print(f"[*] Criterios: {user['sueldo_min']}€, {user['stack']}, {user['ubicacion']}")
    
    # Paso 2: Scrapear ambas fuentes
    print("\n[*] Scrapeando InfoJobs...")
    infojobs_ofertas = fetch_infojobs(user)
    
    print("[*] Scrapeando alertas de LinkedIn...")
    linkedin_ofertas = fetch_linkedin_alerts(user)
    
    # Paso 3: Normalizar y deduplicar
    print("\n[*] Normalizando ofertas...")
    ofertas = merge_sources(infojobs_ofertas, linkedin_ofertas)
    
    # Paso 4: Clasificar y guardar
    print("[*] Clasificando con Claude...")
    buenas = 0
    nuevas_para_notificar = []

    # Mapear claves BD (minúsculas) → claves classifier (mayúsculas)
    user_config = {
        'SUELDO_MIN': str(user['sueldo_min']),
        'STACK': user['stack'],
        'UBICACION': user['ubicacion'],
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
    }

    for oferta in ofertas:
        resultado = classify_oferta(oferta, user_config)

        score = resultado.get('score', 0)
        motivo = resultado.get('motivo', '')
        encaja = resultado.get('encaja', False)

        print(f"  {'✓' if encaja else '✗'} [{score}/10] {oferta['titulo'][:50]}")
        print(f"      → {motivo}")

        if encaja and score >= 7:
            guardada = save_oferta(oferta, user_id, score, motivo)
            if guardada:  # solo notificar si es nueva (INSERT, no IGNORE)
                buenas += 1
                nuevas_para_notificar.append({**oferta, 'score': score, 'motivo': motivo})

    # Paso 5: Notificar por Telegram
    if nuevas_para_notificar:
        notify_ofertas(nuevas_para_notificar, user)

    # Paso 6: Resumen
    print(f"\n[✓] Scraper terminado")
    print(f"  Total procesadas: {len(ofertas)}")
    print(f"  Guardadas y notificadas: {buenas}")
    print(f"  Descartadas: {len(ofertas) - buenas}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Agent Scraper")
    parser.add_argument("--user", required=True, help="Username del usuario")
    args = parser.parse_args()
    
    run_scraper_for_user(args.user)