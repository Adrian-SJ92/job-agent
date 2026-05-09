import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib

DB_PATH = "ofertas.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        chat_id INTEGER UNIQUE,
        sueldo_min INTEGER DEFAULT 20000,
        stack TEXT DEFAULT 'React, JavaScript',
        ubicacion TEXT DEFAULT 'Malaga, remoto',
        email TEXT,
        telegram_token TEXT,
        estado TEXT DEFAULT 'activo',
        fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ofertas (
        id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        titulo TEXT,
        empresa TEXT,
        url TEXT,
        descripcion TEXT,
        fuente TEXT DEFAULT 'infojobs',
        fecha_captura TEXT,
        score INTEGER,
        motivo TEXT,
        estado TEXT DEFAULT 'pendiente',
        fecha_aplicada TEXT,
        feedback TEXT,
        PRIMARY KEY (id, user_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS criterios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        palabra_clave TEXT NOT NULL,
        excluir INTEGER DEFAULT 0,
        peso REAL DEFAULT 1.0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        total_vistas INTEGER DEFAULT 0,
        total_aplicadas INTEGER DEFAULT 0,
        fecha_actualizado TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()


def _row_to_user(row):
    cols = ['id', 'username', 'chat_id', 'sueldo_min', 'stack', 'ubicacion',
            'email', 'telegram_token', 'estado', 'fecha_creacion']
    return dict(zip(cols, row))


def get_user_by_chat_id(chat_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def get_user_by_username(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def create_user(username, chat_id, sueldo_min=20000, stack='React, JavaScript',
                ubicacion='Malaga, remoto', email=None):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            '''INSERT INTO users (username, chat_id, sueldo_min, stack, ubicacion, email)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (username, chat_id, sueldo_min, stack, ubicacion, email)
        )
        user_id = c.lastrowid
        c.execute('INSERT OR IGNORE INTO stats (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return user_id
    except Exception as e:
        print(f"Error creating user: {e}")
        return None
    finally:
        conn.close()


def update_user_config(user_id, **kwargs):
    allowed = {'sueldo_min', 'stack', 'ubicacion', 'email', 'telegram_token', 'estado', 'chat_id'}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    conn = get_conn()
    c = conn.cursor()
    try:
        set_clause = ', '.join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        c.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True
    finally:
        conn.close()


def get_user_ofertas(user_id, estado=None, limit=10):
    conn = get_conn()
    c = conn.cursor()
    cols = ['id', 'titulo', 'empresa', 'url', 'score', 'motivo', 'estado']
    if estado:
        c.execute(
            '''SELECT id, titulo, empresa, url, score, motivo, estado
               FROM ofertas WHERE user_id = ? AND estado = ?
               ORDER BY score DESC LIMIT ?''',
            (user_id, estado, limit)
        )
    else:
        c.execute(
            '''SELECT id, titulo, empresa, url, score, motivo, estado
               FROM ofertas WHERE user_id = ?
               ORDER BY score DESC LIMIT ?''',
            (user_id, limit)
        )
    rows = c.fetchall()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]


def save_oferta(oferta, user_id, score, motivo):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            '''INSERT OR IGNORE INTO ofertas
               (id, user_id, titulo, empresa, url, descripcion, fuente, fecha_captura, score, motivo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (oferta['id'], user_id, oferta['titulo'], oferta['empresa'],
             oferta['url'], oferta['descripcion'], oferta.get('fuente', 'infojobs'),
             datetime.now().isoformat(), score, motivo)
        )
        c.execute(
            '''UPDATE stats SET total_vistas = total_vistas + 1, fecha_actualizado = ?
               WHERE user_id = ?''',
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error guardando oferta: {e}")
        return False
    finally:
        conn.close()


def mark_oferta_aplicada(oferta_id, user_id):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            '''UPDATE ofertas SET estado = 'aplicada', fecha_aplicada = ?
               WHERE id = ? AND user_id = ?''',
            (datetime.now().isoformat(), oferta_id, user_id)
        )
        c.execute(
            '''UPDATE stats SET total_aplicadas = total_aplicadas + 1, fecha_actualizado = ?
               WHERE user_id = ?''',
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_user_stats(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT total_vistas, total_aplicadas FROM stats WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return {'total_vistas': row[0], 'total_aplicadas': row[1]} if row else {'total_vistas': 0, 'total_aplicadas': 0}
