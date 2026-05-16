import asyncio
import os
from typing import List, Dict
from email.utils import parsedate_to_datetime
from datetime import datetime

from telegram import Bot
from telegram.error import TelegramError


def _format_fecha(fecha_raw: str) -> str:
    """Convierte fecha de email a formato legible: 'lun 16 may · 10:12'"""
    try:
        dt = parsedate_to_datetime(fecha_raw)
        dias = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
        meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
        return f"{dias[dt.weekday()]} {dt.day} {meses[dt.month - 1]} · {dt.strftime('%H:%M')}"
    except Exception:
        return fecha_raw[:16] if fecha_raw else ''


def _score_bar(score: int) -> str:
    filled = round(score / 2)
    return '█' * filled + '░' * (5 - filled)


async def _send_messages(token: str, chat_id: int, ofertas: List[Dict], total: int):
    bot = Bot(token=token)

    # Mensaje de cabecera
    now = datetime.now().strftime('%H:%M · %d %b')
    header = (
        f"🔔 *{len(ofertas)} nueva{'s' if len(ofertas) > 1 else ''} oferta{'s' if len(ofertas) > 1 else ''}*\n"
        f"_{now} — Job Agent_"
    )
    try:
        await bot.send_message(chat_id=chat_id, text=header, parse_mode="Markdown")
    except TelegramError as e:
        print(f"[Telegram] Error enviando cabecera: {e}")

    # Una notificación por oferta
    for i, oferta in enumerate(ofertas, 1):
        score = oferta['score']
        fecha = _format_fecha(oferta.get('fecha_publicacion', ''))
        url_line = f"\n🔗 [Ver oferta]({oferta['url']})" if oferta.get('url') else ""
        fuente = oferta.get('fuente', 'linkedin').capitalize()

        text = (
            f"*{i}/{len(ofertas)}* — {fuente}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💼 *{oferta['titulo']}*\n"
            f"🏢 {oferta['empresa']}\n"
            f"📅 {fecha}\n"
            f"\n"
            f"⭐ Score: *{score}/10*  `{_score_bar(score)}`\n"
            f"💬 _{oferta['motivo']}_"
            f"{url_line}"
        )
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except TelegramError as e:
            print(f"[Telegram] Error enviando oferta '{oferta['titulo']}': {e}")


def notify_ofertas(ofertas: List[Dict], user: Dict):
    """Envía notificaciones Telegram para las ofertas guardadas.

    Args:
        ofertas: lista de dicts con keys titulo, empresa, score, motivo, url
        user: dict del usuario de BD (necesita chat_id y telegram_token)
    """
    if not ofertas:
        return

    token = os.getenv('TELEGRAM_BOT_TOKEN') or user.get('telegram_token', '')
    chat_id = user.get('chat_id')

    if not token:
        print("[Telegram] Sin token, notificaciones desactivadas")
        return
    if not chat_id:
        print("[Telegram] Sin chat_id, usa /setup en el bot primero")
        return

    print(f"[Telegram] Enviando {len(ofertas)} notificaciones...")
    try:
        asyncio.run(_send_messages(token, chat_id, ofertas, len(ofertas)))
        print(f"[Telegram] Notificaciones enviadas")
    except Exception as e:
        print(f"[Telegram] Error: {e}")
