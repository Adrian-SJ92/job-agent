"""
Prueba de la refactorizacion multiusuario.
Corre desde la raiz del proyecto:
    python tests/test_multiuser.py
"""
import os
import sys
import json
import tempfile

# Asegurarse de que el proyecto esta en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ERRORS = []

def ok(msg):
    print(f"  [OK] {msg}")

def fail(msg, e=None):
    detail = f" -> {e}" if e else ""
    print(f"  [FAIL] {msg}{detail}")
    ERRORS.append(msg)


# ─────────────────────────────────────────────
# 1. Imports
# ─────────────────────────────────────────────
print("\n=== 1. Imports ===")
try:
    from job_agent.db.schema import (
        init_db, create_user, get_user_by_username,
        get_user_by_chat_id, update_user_config,
        get_user_stats, get_user_ofertas, save_oferta, mark_oferta_aplicada
    )
    ok("job_agent.db.schema")
except Exception as e:
    fail("job_agent.db.schema", e)

try:
    from job_agent.config.config_manager import load_users_index, load_user_config, get_all_usernames
    ok("job_agent.config.config_manager")
except Exception as e:
    fail("job_agent.config.config_manager", e)

try:
    from job_agent.classifier import classify_oferta, classifier_prompt
    ok("job_agent.classifier")
except Exception as e:
    fail("job_agent.classifier", e)

try:
    from job_agent.scraper import fetch_infojobs, build_rss_url
    ok("job_agent.scraper")
except Exception as e:
    fail("job_agent.scraper", e)

try:
    from job_agent.telegram_bot import SETUP_USERNAME, SETUP_SUELDO
    ok("job_agent.telegram_bot")
except Exception as e:
    fail("job_agent.telegram_bot", e)


# ─────────────────────────────────────────────
# 2. DB: init + CRUD
# ─────────────────────────────────────────────
print("\n=== 2. Base de datos ===")
try:
    import job_agent.db.schema as schema
    # Usar BD temporal para no contaminar la real
    schema.DB_PATH = tempfile.mktemp(suffix=".db")
    init_db()
    ok("init_db() - tablas creadas")
except Exception as e:
    fail("init_db()", e)

try:
    uid = create_user(
        username="test_user",
        chat_id=999999999,
        sueldo_min=22000,
        stack="React, TypeScript",
        ubicacion="Malaga, remoto",
        email="test@example.com"
    )
    assert uid is not None, "create_user devolvio None"
    ok(f"create_user() -> user_id={uid}")
except Exception as e:
    fail("create_user()", e)
    uid = None

try:
    u = get_user_by_username("test_user")
    assert u is not None
    assert u['username'] == "test_user"
    assert u['sueldo_min'] == 22000
    ok(f"get_user_by_username() -> {u['username']}, sueldo={u['sueldo_min']}")
except Exception as e:
    fail("get_user_by_username()", e)

try:
    u = get_user_by_chat_id(999999999)
    assert u is not None
    assert u['chat_id'] == 999999999
    ok(f"get_user_by_chat_id() -> chat_id={u['chat_id']}")
except Exception as e:
    fail("get_user_by_chat_id()", e)

try:
    if uid:
        update_user_config(uid, sueldo_min=25000, stack="Vue, Nuxt")
        u = get_user_by_username("test_user")
        assert u['sueldo_min'] == 25000
        assert u['stack'] == "Vue, Nuxt"
        ok("update_user_config() -> sueldo y stack actualizados")
except Exception as e:
    fail("update_user_config()", e)

try:
    if uid:
        oferta = {
            'id': 'oferta-test-001',
            'titulo': 'Frontend Developer',
            'empresa': 'Empresa Test',
            'url': 'https://example.com/oferta/1',
            'descripcion': 'React, TypeScript, buenas condiciones',
            'fuente': 'infojobs'
        }
        result = save_oferta(oferta, uid, score=8, motivo="Buen encaje tecnico")
        assert result is True
        ok("save_oferta() -> guardada correctamente")

        ofertas = get_user_ofertas(uid, estado='pendiente')
        assert len(ofertas) == 1
        assert ofertas[0]['titulo'] == 'Frontend Developer'
        ok(f"get_user_ofertas() -> {len(ofertas)} oferta(s) encontrada(s)")
except Exception as e:
    fail("save_oferta() / get_user_ofertas()", e)

try:
    if uid:
        stats = get_user_stats(uid)
        assert stats['total_vistas'] == 1
        ok(f"get_user_stats() -> vistas={stats['total_vistas']}, aplicadas={stats['total_aplicadas']}")
except Exception as e:
    fail("get_user_stats()", e)

try:
    if uid:
        mark_oferta_aplicada('oferta-test-001', uid)
        stats = get_user_stats(uid)
        assert stats['total_aplicadas'] == 1
        ok(f"mark_oferta_aplicada() -> aplicadas={stats['total_aplicadas']}")
except Exception as e:
    fail("mark_oferta_aplicada()", e)

# Limpiar BD temporal
try:
    os.remove(schema.DB_PATH)
except Exception:
    pass


# ─────────────────────────────────────────────
# 3. Config manager (con users.json.example)
# ─────────────────────────────────────────────
print("\n=== 3. Config Manager ===")
try:
    import job_agent.config.config_manager as cm
    from pathlib import Path

    # Apuntar al directorio config del proyecto
    cm.CONFIG_DIR = Path("config")
    cm.USERS_JSON = cm.CONFIG_DIR / "users.json.example"

    data = load_users_index()
    assert "users" in data
    assert len(data["users"]) > 0
    ok(f"load_users_index() con .example -> {len(data['users'])} usuario(s)")

    names = get_all_usernames()
    ok(f"get_all_usernames() -> {names}")
except Exception as e:
    fail("config_manager con users.json.example", e)


# ─────────────────────────────────────────────
# 4. Classifier prompt (sin llamada a API)
# ─────────────────────────────────────────────
print("\n=== 4. Classifier prompt ===")
try:
    oferta = {
        'titulo': 'Frontend Developer Junior',
        'empresa': 'Startup Malaga',
        'descripcion': 'React, TypeScript, 22k, remoto'
    }
    user_config = {
        'SUELDO_MIN': '20000',
        'STACK': 'React, TypeScript',
        'UBICACION': 'Malaga, remoto'
    }
    prompt = classifier_prompt(oferta, user_config)
    assert 'React' in prompt
    assert '20000' in prompt
    assert 'Frontend Developer Junior' in prompt
    ok("classifier_prompt() genera prompt correcto con config de usuario")
except Exception as e:
    fail("classifier_prompt()", e)


# ─────────────────────────────────────────────
# 5. Scraper: build_rss_url
# ─────────────────────────────────────────────
print("\n=== 5. Scraper ===")
try:
    user_config = {
        'RSS_KEYWORDS': 'react typescript',
        'RSS_CITY': 'malaga',
        'RSS_EXPERIENCE': 'junior'
    }
    url = build_rss_url(user_config)
    assert 'infojobs.net' in url
    assert 'react' in url
    assert 'malaga' in url
    ok(f"build_rss_url() -> {url}")
except Exception as e:
    fail("build_rss_url()", e)


# ─────────────────────────────────────────────
# Resultado final
# ─────────────────────────────────────────────
print("\n" + "="*45)
if ERRORS:
    print(f"RESULTADO: {len(ERRORS)} error(es) encontrado(s):")
    for e in ERRORS:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("RESULTADO: Todos los tests pasaron correctamente.")
