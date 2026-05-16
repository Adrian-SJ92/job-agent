import sys
import argparse
from .infojobs import fetch_infojobs
from .gmail import fetch_linkedin_alerts
from .normalizer import merge_sources
from job_agent.db.schema import get_user_by_username, save_oferta
from job_agent.classifier import classify_oferta

def run_scraper_for_user(username: str):
    """
    Ejecuta el scraper completo para un usuario.
    1. Obtiene credenciales del usuario
    2. Scrappea InfoJobs + LinkedIn
    3. Clasifica con Claude
    4. Guarda en BD
    """

    # Paso 1: Obtener usuario de BD y combinar con config del .env
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
    
    for oferta in ofertas:
        # Clasificar
        resultado = classify_oferta(oferta)
        
        score = resultado.get('score', 0)
        motivo = resultado.get('motivo', '')
        encaja = resultado.get('encaja', False)

        print(f"  {'✓' if encaja else '✗'} [{score}/10] {oferta['titulo'][:50]}")
        print(f"      → {motivo}")

        if encaja:
            buenas += 1
            save_oferta(oferta, user_id, score, motivo)
    
    # Paso 5: Resumen
    print(f"\n[✓] Scraper terminado")
    print(f"  Total procesadas: {len(ofertas)}")
    print(f"  Guardadas: {buenas}")
    print(f"  Descartadas: {len(ofertas) - buenas}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Agent Scraper")
    parser.add_argument("--user", required=True, help="Username del usuario")
    args = parser.parse_args()
    
    run_scraper_for_user(args.user)