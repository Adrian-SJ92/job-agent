<div align="center">

# 🤖 Job Agent

### Automatiza tu búsqueda de empleo con Python

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram_Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*Deja que el bot encuentre tu próximo trabajo mientras tú te centras en lo importante.*

</div>

---

## ✨ ¿Qué hace?

Job Agent es un asistente personal de búsqueda de empleo que trabaja por ti de forma autónoma:

- 🔍 **Escanea** ofertas de InfoJobs continuamente vía RSS
- 🧠 **Filtra y puntúa** cada oferta según tus criterios personales (stack, salario, ubicación)
- 👥 **Multi-usuario** — cada persona tiene su propia configuración, criterios y datos aislados
- 💾 **Almacena** las mejores oportunidades en una base de datos local
- 📱 **Interfaz Telegram** para revisar ofertas, ver estadísticas y gestionar candidaturas
- 📄 **Genera** CVs y cartas de presentación personalizadas *(próximamente)*

---

## 🏗️ Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  InfoJobs   │────▶│  scraper.py  │────▶│classifier.py │────▶│  ofertas.db  │
│  RSS Feed   │     │  --user foo  │     │  (scoring)   │     │  (SQLite)    │
└─────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                          ┌────────────────────┐                       ▼
                          │ config/users.json  │──────▶   ┌──────────────────┐
                          │ config/foo.env     │           │  telegram_bot.py │
                          └────────────────────┘           │  --user foo      │
                                                           └──────────────────┘
```

| Módulo | Descripción |
|--------|-------------|
| `scraper.py` | Obtiene ofertas de InfoJobs vía RSS y las clasifica para un usuario concreto (`--user`) |
| `classifier.py` | Puntúa cada oferta del 0 al 10 usando los criterios del usuario (sueldo, stack, ubicación) |
| `telegram_bot.py` | Bot asíncrono con teclado inline, registro de usuarios y gestión de ofertas |
| `db/schema.py` | Capa de acceso a datos: tablas `users`, `ofertas`, `criterios` y `stats` |
| `config/config_manager.py` | Carga la configuración por usuario desde `config/users.json` y su `.env` |

---

## 📱 Bot de Telegram

| Comando | Descripción |
|---------|-------------|
| `/start` | Menú principal (requiere estar registrado) |
| `/setup` | Asistente de registro: nombre, sueldo mínimo, stack, ubicación y email |
| `/pendientes` | Lista las 5 mejores ofertas pendientes de decisión |
| `/stats` | Estadísticas personales: ofertas vistas y candidaturas enviadas |
| `/cv [id]` | Genera un CV adaptado a esa oferta *(próximamente)* |
| `/carta [id]` | Redacta una carta de presentación personalizada *(próximamente)* |

---

## ⚡ Inicio rápido

### 1. Clonar e instalar

```bash
git clone https://github.com/Adrian-SJ92/job-agent.git
cd job-agent

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar usuarios

Crea el fichero `config/users.json` con tus usuarios:

```json
{
  "users": [
    {
      "username": "foo",
      "chat_id": 123456789,
      "telegram_token": "TU_BOT_TOKEN",
      "config_file": "foo.env"
    }
  ]
}
```

Crea `config/foo.env` con las credenciales y criterios del usuario:

```env
ANTHROPIC_API_KEY=tu_api_key_aqui
GMAIL_USER=tu_email@gmail.com
GMAIL_PASSWORD=tu_app_password

# Criterios de búsqueda (opcionales, tienen valores por defecto)
SUELDO_MIN=20000
STACK=React, Node.js, TypeScript
UBICACION=Malaga, remoto o hibrido en España
RSS_KEYWORDS=react
RSS_CITY=malaga
RSS_EXPERIENCE=junior
```

> `config/users.json` y los ficheros `.env` están en `.gitignore` — tus credenciales nunca se subirán al repo.

### 3. Registrar el usuario en el bot

Arranca el bot y ejecuta `/setup` desde Telegram para crear tu cuenta en la base de datos:

```bash
python -m job_agent.telegram_bot --user foo
```

### 4. Lanzar el scraper

```bash
python -m job_agent.scraper --user foo
```

---

## ⚙️ Personalización de criterios

Los criterios de filtrado se configuran por usuario en su fichero `.env`. No hace falta tocar el código.

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SUELDO_MIN` | Sueldo mínimo anual en EUR | `20000` |
| `STACK` | Tecnologías preferidas | `React, Node.js, TypeScript` |
| `UBICACION` | Ubicación o modalidad aceptada | `Malaga, remoto o hibrido` |
| `RSS_KEYWORDS` | Términos de búsqueda en InfoJobs | `react typescript` |
| `RSS_CITY` | Ciudad en InfoJobs | `malaga` |
| `RSS_EXPERIENCE` | Nivel de experiencia | `junior` |

---

## 🗄️ Esquema de base de datos

```sql
-- Un registro por usuario registrado en el bot
CREATE TABLE users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT UNIQUE NOT NULL,
    chat_id        INTEGER UNIQUE,
    sueldo_min     INTEGER DEFAULT 20000,
    stack          TEXT,
    ubicacion      TEXT,
    email          TEXT,
    estado         TEXT DEFAULT 'activo'
);

-- Ofertas indexadas por usuario (clave compuesta id + user_id)
CREATE TABLE ofertas (
    id             TEXT NOT NULL,
    user_id        INTEGER NOT NULL,
    titulo         TEXT,
    empresa        TEXT,
    url            TEXT,
    score          INTEGER,      -- 0-10
    motivo         TEXT,
    estado         TEXT DEFAULT 'pendiente',  -- 'pendiente' | 'aplicada'
    fecha_aplicada TEXT,
    PRIMARY KEY (id, user_id)
);

-- Estadísticas por usuario (actualizadas automáticamente)
CREATE TABLE stats (
    user_id         INTEGER UNIQUE,
    total_vistas    INTEGER DEFAULT 0,
    total_aplicadas INTEGER DEFAULT 0
);
```

---

## 🛠️ Stack tecnológico

- **[Python 3.13+](https://python.org)** — lenguaje principal
- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)** — bot asíncrono con `ConversationHandler`
- **[feedparser](https://feedparser.readthedocs.io)** — parsing de RSS
- **[SQLite3](https://sqlite.org)** — base de datos local, sin servidor
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — gestión de variables de entorno por usuario

---

## 🗺️ Roadmap

- [x] Scraper de InfoJobs vía RSS
- [x] Clasificación y puntuación automática de ofertas
- [x] Bot de Telegram interactivo con teclado inline
- [x] Sistema multi-usuario con configuración y datos aislados
- [x] Registro de usuarios vía `/setup` desde Telegram
- [x] Estadísticas de búsqueda por usuario
- [ ] Generación de CV personalizado por oferta
- [ ] Cartas de presentación adaptadas
- [ ] Soporte para LinkedIn y otras fuentes
- [ ] Notificaciones automáticas de nuevas ofertas
- [ ] Historial de candidaturas y seguimiento

---

<div align="center">

Hecho con ☕ y Python · ¿Ideas o bugs? Abre un [issue](https://github.com/Adrian-SJ92/job-agent/issues)

</div>
