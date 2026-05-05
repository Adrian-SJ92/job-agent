import os
from dotenv import load_dotenv
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from job_agent.classifier import classify_oferta
from anthropic import Anthropic
from job_agent.classifier import classify_oferta

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
DB_PATH = "ofertas.db"

client = Anthropic()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    keyboard = [
        [InlineKeyboardButton("📋 Ver pendientes", callback_data="pendientes")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *Job Agent* activado\n\n"
        "Búsqueda automática de ofertas con IA.\n\n"
        "Comandos:\n"
        "/pendientes - Ofertas sin decisión\n"
        "/stats - Estadísticas\n"
        "/help - Ayuda",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja botones inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "pendientes":
        await mostrar_pendientes(query)
    elif query.data == "stats":
        await mostrar_stats(query)
    elif query.data == "help":
        await mostrar_help(query)

async def mostrar_pendientes(query):
    """Muestra ofertas pendientes"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, titulo, empresa, score FROM ofertas WHERE estado='pendiente' LIMIT 5")
    ofertas = c.fetchall()
    conn.close()
    
    if not ofertas:
        await query.edit_message_text("✅ Sin ofertas pendientes")
        return
    
    texto = "📋 *Ofertas Pendientes*\n\n"
    for id_of, titulo, empresa, score in ofertas:
        texto += f"*{titulo}* ({score}/10)\n{empresa}\n/ver_{id_of}\n\n"
    
    await query.edit_message_text(texto, parse_mode="Markdown")

async def mostrar_stats(query):
    """Muestra estadísticas"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ofertas")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ofertas WHERE estado='aplicada'")
    aplicadas = c.fetchone()[0]
    conn.close()
    
    texto = f"📊 *Estadísticas*\n\nTotal vistas: {total}\nAplicadas: {aplicadas}"
    await query.edit_message_text(texto, parse_mode="Markdown")

async def mostrar_help(query):
    """Muestra ayuda"""
    await query.edit_message_text(
        "❓ *Ayuda*\n\n"
        "/start - Menú principal\n"
        "/pendientes - Ver ofertas\n"
        "/stats - Estadísticas\n"
        "/cv [id] - Generar CV\n"
        "/carta [id] - Generar carta",
        parse_mode="Markdown"
    )

def start_bot():
    """Inicia el bot"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.run_polling()

if __name__ == "__main__":
    start_bot()
