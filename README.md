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
- 💾 **Almacena** las mejores oportunidades en una base de datos local
- 📱 **Te notifica** y permite interactuar con las ofertas desde Telegram
- 📄 **Genera** CVs y cartas de presentación personalizadas *(próximamente)*

---

## 🏗️ Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  InfoJobs   │────▶│  scraper.py  │────▶│classifier.py │────▶│  ofertas.db  │
│  RSS Feed   │     │  (fetching)  │     │  (scoring)   │     │  (SQLite)    │
└─────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                                                                       ▼
                                                              ┌──────────────────┐
                                                              │  telegram_bot.py │
                                                              │  (interfaz user) │
                                                              └──────────────────┘
```

| Módulo | Descripción |
|--------|-------------|
| `scraper.py` | Obtiene ofertas de InfoJobs vía RSS con `feedparser` y orquesta el pipeline completo |
| `classifier.py` | Puntúa cada oferta del 0 al 10 según tus criterios configurables |
| `telegram_bot.py` | Bot asíncrono con teclado inline para revisar, gestionar y actuar sobre las ofertas |

---

## 📱 Bot de Telegram

El bot expone los siguientes comandos:

| Comando | Descripción |
|---------|-------------|
| `/start` | Menú principal con accesos rápidos |
| `/pendientes` | Lista las ofertas sin decisión |
| `/stats` | Estadísticas: total vistas, aplicadas, score medio |
| `/cv [id]` | Genera un CV adaptado a esa oferta concreta |
| `/carta [id]` | Redacta una carta de presentación personalizada |

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

### 2. Configurar credenciales

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
ANTHROPIC_API_KEY=tu_api_key_aqui
GMAIL_USER=tu_email@gmail.com
GMAIL_PASSWORD=tu_app_password
```

> **¿Cómo conseguir el token de Telegram?** Habla con [@BotFather](https://t.me/BotFather) en Telegram y crea un bot nuevo.

### 3. Ejecutar

```bash
# Lanzar el scraper (busca, clasifica y guarda ofertas)
python -m job_agent.scraper

# Lanzar el bot de Telegram (interfaz interactiva)
python -m job_agent.telegram_bot
```

---

## ⚙️ Personalización

### Criterios de clasificación

Edita `job_agent/classifier.py` para ajustar qué considera una buena oferta:

```python
# Criterios actuales (classifier.py:11-16)
- Sueldo mínimo: 20.000 € anuales
- Rol: Frontend Junior (flexible en stack)
- Ubicación: Málaga, remoto o híbrido en España
- Stack preferido: React, Node.js, JavaScript, Python
- Empresa: Startup/Scale-up (evitar consultoras grandes)
```

### Búsqueda en InfoJobs

Modifica la URL RSS en `job_agent/scraper.py:10` para cambiar los términos de búsqueda:

```python
INFOJOBS_RSS = "https://www.infojobs.net/rss/search?q=react&city=malaga&experience=junior"
#                                                     ^^^^        ^^^^^^             ^^^^^^
#                                                  búsqueda     ciudad            experiencia
```

---

## 🗄️ Esquema de base de datos

```sql
CREATE TABLE ofertas (
    id             TEXT PRIMARY KEY,
    titulo         TEXT,
    empresa        TEXT,
    url            TEXT,
    descripcion    TEXT,
    fecha_captura  TEXT,
    score          INTEGER,   -- 0-10, puntuación automática
    motivo         TEXT,      -- razón del score en una línea
    estado         TEXT DEFAULT 'pendiente'  -- 'pendiente' | 'aplicada'
);
```

---

## 🛠️ Stack tecnológico

- **[Python 3.13+](https://python.org)** — lenguaje principal
- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)** — bot asíncrono
- **[feedparser](https://feedparser.readthedocs.io)** — parsing de RSS
- **[SQLite3](https://sqlite.org)** — base de datos local, sin servidor
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — gestión de variables de entorno

---

## 🗺️ Roadmap

- [x] Scraper de InfoJobs vía RSS
- [x] Clasificación y puntuación automática de ofertas
- [x] Bot de Telegram interactivo con teclado inline
- [ ] Generación de CV personalizado por oferta
- [ ] Cartas de presentación adaptadas
- [ ] Soporte para LinkedIn y otras fuentes
- [ ] Notificaciones automáticas de nuevas ofertas
- [ ] Historial de aplicaciones y seguimiento

---

<div align="center">

Hecho con ☕ y Python · ¿Ideas o bugs? Abre un [issue](https://github.com/Adrian-SJ92/job-agent/issues)

</div>
