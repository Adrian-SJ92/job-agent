import asyncio
import os
from typing import List, Dict

from telegram import Bot
from telegram.error import TelegramError


async def _send_messages(token: str, chat_id: int, ofertas: List[Dict]):
    bot = Bot(token=token)
    for oferta in ofertas:
        url_line = f"\n🔗 {oferta['url']}" if oferta.get('url') else ""
        text = (
            f"💼 *{oferta['titulo']}*\n"
            f"🏢 {oferta['empresa']}\n"
            f"⭐ Score: {oferta['score']}/10\n"
            f"📝 {oferta['motivo']}"
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
        asyncio.run(_send_messages(token, chat_id, ofertas))
        print(f"[Telegram] Notificaciones enviadas")
    except Exception as e:
        print(f"[Telegram] Error: {e}")
