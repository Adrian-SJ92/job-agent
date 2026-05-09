#!/bin/bash
# install_services.sh — Instala los servicios systemd para job-agent en la Raspberry Pi

set -e

# ── Configuración ──────────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
USER_NAME="$(whoami)"
# ──────────────────────────────────────────────────────────────────────────────

echo "Instalando servicios job-agent..."
echo "  Directorio: $PROJECT_DIR"
echo "  Usuario:    $USER_NAME"
echo ""

# Verificaciones previas
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: No se encontró el venv en $VENV_PYTHON"
    echo "Ejecuta primero: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "ERROR: No se encontró el archivo .env en $PROJECT_DIR"
    echo "Ejecuta primero: cp .env.example .env  y rellena las credenciales"
    exit 1
fi

# ── Servicio: Telegram Bot ─────────────────────────────────────────────────────
sudo tee /etc/systemd/system/job-agent-bot.service > /dev/null <<EOF
[Unit]
Description=Job Agent Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PYTHON -m job_agent.telegram_bot
Restart=always
RestartSec=10
EnvironmentFile=$PROJECT_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

echo "Creado: job-agent-bot.service"

# ── Servicio: Scraper ──────────────────────────────────────────────────────────
sudo tee /etc/systemd/system/job-agent-scraper.service > /dev/null <<EOF
[Unit]
Description=Job Agent Scraper
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PYTHON -m job_agent.scraper
Restart=on-failure
RestartSec=60
EnvironmentFile=$PROJECT_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

echo "Creado: job-agent-scraper.service"

# ── Timer: Scraper cada 4 horas ────────────────────────────────────────────────
sudo tee /etc/systemd/system/job-agent-scraper.timer > /dev/null <<EOF
[Unit]
Description=Ejecutar Job Agent Scraper cada 4 horas

[Timer]
OnBootSec=2min
OnUnitActiveSec=4h

[Install]
WantedBy=timers.target
EOF

echo "Creado: job-agent-scraper.timer"

# ── Activar todo ───────────────────────────────────────────────────────────────
sudo systemctl daemon-reload

sudo systemctl enable job-agent-bot
sudo systemctl start job-agent-bot

sudo systemctl enable job-agent-scraper.timer
sudo systemctl start job-agent-scraper.timer

echo ""
echo "Servicios instalados y activos."
echo ""
echo "Comandos utiles:"
echo "  sudo systemctl status job-agent-bot"
echo "  sudo journalctl -u job-agent-bot -f"
echo "  sudo journalctl -u job-agent-scraper -f"
echo "  sudo systemctl list-timers job-agent-scraper.timer"
