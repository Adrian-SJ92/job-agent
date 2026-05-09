import argparse
from job_agent.scrapers.infojobs import fetch_infojobs
from job_agent.classifier import classify_oferta
from job_agent.config.config_manager import load_user_config
from job_agent.db.schema import init_db, get_user_by_username, save_oferta


def main():
    parser = argparse.ArgumentParser(description='Job Agent Scraper')
    parser.add_argument('--user', required=True, help='Username to run scraper for')
    args = parser.parse_args()

    print(f"[*] Cargando config para usuario: {args.user}")
    user_config = load_user_config(args.user)

    init_db()

    user = get_user_by_username(args.user)
    if not user:
        print(f"[!] Usuario '{args.user}' no encontrado en la BD.")
        print("    Inicia el bot y usa /setup para registrarte primero.")
        return

    user_id = user['id']

    print(f"[*] Capturando ofertas de InfoJobs...")
    ofertas = fetch_infojobs(user_config)
    print(f"[*] {len(ofertas)} ofertas encontradas")

    buenas = 0
    for oferta in ofertas:
        print(f"  Analizando: {oferta['titulo'][:50]}...")
        resultado = classify_oferta(oferta, user_config)

        if resultado['encaja']:
            buenas += 1
            save_oferta(oferta, user_id, resultado['score'], resultado['motivo'])
            print(f"    OK Score {resultado['score']}: {resultado['motivo']}")
        else:
            print(f"    X Descartada: {resultado['motivo']}")

    print(f"\n[OK] Proceso terminado: {buenas} ofertas validas de {len(ofertas)}")


if __name__ == "__main__":
    main()
