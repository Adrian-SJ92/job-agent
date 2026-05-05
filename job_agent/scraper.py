import feedparser
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os
from job_agent.classifier import classify_oferta

load_dotenv()

INFOJOBS_RSS = "https://www.infojobs.net/rss/search?q=react&city=malaga&experience=junior"
DB_PATH = "ofertas.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ofertas
                 (id TEXT PRIMARY KEY, titulo TEXT, empresa TEXT, url TEXT, 
                  descripcion TEXT, fecha_captura TEXT, score INTEGER, 
                  motivo TEXT, estado TEXT DEFAULT 'pendiente')''')
    conn.commit()
    conn.close()

def fetch_infojobs():
    feed = feedparser.parse(INFOJOBS_RSS)
    ofertas = []
    for entry in feed.entries:
        oferta = {
            'id': entry.get('id', ''),
            'titulo': entry.get('title', ''),
            'empresa': entry.get('author', 'Desconocida'),
            'url': entry.get('link', ''),
            'descripcion': entry.get('summary', ''),
            'fuente': 'infojobs'
        }
        ofertas.append(oferta)
    return ofertas

def save_oferta(oferta, score, motivo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''INSERT OR IGNORE INTO ofertas 
                     (id, titulo, empresa, url, descripcion, fecha_captura, score, motivo)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (oferta['id'], oferta['titulo'], oferta['empresa'], 
                   oferta['url'], oferta['descripcion'], 
                   datetime.now().isoformat(), score, motivo))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error guardando: {e}")
        return False
    finally:
        conn.close()

def main():
    init_db()
    print("[*] Capturando ofertas de InfoJobs...")
    ofertas = fetch_infojobs()
    print(f"[*] {len(ofertas)} ofertas encontradas")
    
    buenas = 0
    for oferta in ofertas:
        print(f"  Analizando: {oferta['titulo'][:50]}...")
        resultado = classify_oferta(oferta)
        
        if resultado['encaja']:
            buenas += 1
            save_oferta(oferta, resultado['score'], resultado['motivo'])
            print(f"    ✓ Score {resultado['score']}: {resultado['motivo']}")
        else:
            print(f"    ✗ Descartada: {resultado['motivo']}")
    
    print(f"\n[✓] Proceso terminado: {buenas} ofertas válidas")

if __name__ == "__main__":
    main()
