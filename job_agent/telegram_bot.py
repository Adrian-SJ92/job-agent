import argparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from job_agent.db.schema import (
    init_db, get_user_by_chat_id, create_user, update_user_config,
    get_user_ofertas, get_user_stats
)
from job_agent.config.config_manager import load_user_config

# ConversationHandler states
SETUP_USERNAME, SETUP_SUELDO, SETUP_STACK, SETUP_UBICACION, SETUP_EMAIL = range(5)
CONFIG_FIELD, CONFIG_VALUE = range(5, 7)


def _get_user(update: Update):
    return get_user_by_chat_id(update.effective_chat.id)


# --- /start ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _get_user(update)
    if not user:
        await update.message.reply_text(
            "Bienvenido a *Job Agent*\n\n"
            "No estas registrado. Usa /setup para configurar tu cuenta.",
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton("Ver pendientes", callback_data="pendientes")],
        [InlineKeyboardButton("Stats", callback_data="stats")],
        [InlineKeyboardButton("Ayuda", callback_data="help")],
    ]
    await update.message.reply_text(
        "🤖 *Job Agent* — Tu co-piloto en la búsqueda de empleo\n\n"
        f"¡Hola {user['username']}! 👋\n\n"
        "Soy tu asistente de IA para encontrar trabajo. Analizo ofertas, genero CVs personalizados y te ayudo a estar un paso adelante.\n\n"
        "⚡ *Lo que puedo hacer:*\n"
        "🔍 Filtrar ofertas automáticamente (score, sueldo, stack, ubicación)\n"
        "📄 Generar CV adaptado a cada oferta\n"
        "✍️ Redactar cartas de presentación personalizadas\n"
        "📊 Estadísticas de tu búsqueda\n"
        "🎯 Prepararte para entrevistas\n"
        "💾 Trackear tus candidaturas\n\n"
        "🎬 *Empecemos:*\n"
        "→ /help — Ver todos los comandos\n"
        "→ /pendientes — Ver ofertas disponibles\n"
        "→ /stats — Tus estadísticas\n\n"
        "🎯 Tu siguiente oportunidad está más cerca de lo que crees. ¡Vamos a por ella!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# --- /setup conversation ---

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Configuracion de cuenta*\n\n"
        "Cual sera tu nombre de usuario? (solo letras y numeros, sin espacios)",
        parse_mode="Markdown"
    )
    return SETUP_USERNAME


async def setup_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lower()
    if not username.isalnum():
        await update.message.reply_text("Solo letras y numeros, sin espacios. Intentalo de nuevo:")
        return SETUP_USERNAME
    context.user_data['setup_username'] = username
    await update.message.reply_text("Sueldo minimo anual (EUR)? Ejemplo: 20000")
    return SETUP_SUELDO


async def setup_sueldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sueldo = int(update.message.text.strip().replace('.', '').replace(',', ''))
    except ValueError:
        await update.message.reply_text("Introduce un numero valido:")
        return SETUP_SUELDO
    context.user_data['setup_sueldo'] = sueldo
    await update.message.reply_text("Stack tecnologico preferido? Ejemplo: React, Node.js, TypeScript")
    return SETUP_STACK


async def setup_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['setup_stack'] = update.message.text.strip()
    await update.message.reply_text("Ubicacion/modalidad? Ejemplo: Malaga, remoto o hibrido")
    return SETUP_UBICACION


async def setup_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['setup_ubicacion'] = update.message.text.strip()
    await update.message.reply_text("Email de contacto:")
    return SETUP_EMAIL


async def setup_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    d['setup_email'] = update.message.text.strip()
    chat_id = update.effective_chat.id

    existing = get_user_by_chat_id(chat_id)
    if existing:
        update_user_config(
            existing['id'],
            sueldo_min=d['setup_sueldo'],
            stack=d['setup_stack'],
            ubicacion=d['setup_ubicacion'],
            email=d['setup_email']
        )
        msg = "Configuracion actualizada."
    else:
        create_user(
            username=d['setup_username'],
            chat_id=chat_id,
            sueldo_min=d['setup_sueldo'],
            stack=d['setup_stack'],
            ubicacion=d['setup_ubicacion'],
            email=d['setup_email']
        )
        msg = f"Usuario *{d['setup_username']}* registrado correctamente."

    await update.message.reply_text(msg + "\n\nUsa /start para ver el menu.", parse_mode="Markdown")
    return ConversationHandler.END


async def setup_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Setup cancelado.")
    return ConversationHandler.END


# --- /config ---

CONFIG_FIELDS = {
    'sueldo': ('sueldo_min', 'Sueldo mínimo anual (EUR). Ejemplo: 25000'),
    'stack':  ('stack',      'Stack tecnológico. Ejemplo: React, Node.js, TypeScript, Python'),
    'ubicacion': ('ubicacion', 'Ubicación/modalidad. Ejemplo: Málaga, remoto o híbrido'),
    'email':  ('email',      'Email de contacto'),
}


async def config_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _get_user(update)
    if not user:
        await update.message.reply_text("Usa /setup para registrarte primero.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f.capitalize(), callback_data=f"cfg_{f}")] for f in CONFIG_FIELDS]
    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cfg_cancel")])

    text = (
        f"*Configuración actual*\n\n"
        f"💰 Sueldo mín: {user['sueldo_min']}€\n"
        f"🛠 Stack: {user['stack']}\n"
        f"📍 Ubicación: {user['ubicacion']}\n"
        f"📧 Email: {user['email'] or '—'}\n\n"
        f"¿Qué quieres editar?"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CONFIG_FIELD


async def config_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cfg_cancel":
        await query.edit_message_text("Cancelado.")
        return ConversationHandler.END

    field = query.data.replace("cfg_", "")
    if field not in CONFIG_FIELDS:
        return ConversationHandler.END

    context.user_data['config_field'] = field
    _, prompt = CONFIG_FIELDS[field]
    await query.edit_message_text(f"*Editar {field}*\n\n{prompt}", parse_mode="Markdown")
    return CONFIG_VALUE


async def config_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get('config_field')
    if not field or field not in CONFIG_FIELDS:
        return ConversationHandler.END

    db_field, _ = CONFIG_FIELDS[field]
    value = update.message.text.strip()

    if field == 'sueldo':
        try:
            value = int(value.replace('.', '').replace(',', ''))
        except ValueError:
            await update.message.reply_text("Introduce un número válido:")
            return CONFIG_VALUE

    user = _get_user(update)
    update_user_config(user['id'], **{db_field: value})
    await update.message.reply_text(
        f"✅ *{field.capitalize()}* actualizado.\n\nUsa /config para seguir editando o /start para volver al menú.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def config_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado.")
    return ConversationHandler.END


# --- /pendientes ---

async def pendientes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _get_user(update)
    if not user:
        await update.message.reply_text("Usa /setup para registrarte primero.")
        return
    text = _pendientes_text(user['id'])
    await update.message.reply_text(text, parse_mode="Markdown")


def _pendientes_text(user_id):
    ofertas = get_user_ofertas(user_id, estado='pendiente', limit=5)
    if not ofertas:
        return "Sin ofertas pendientes"
    text = "*Ofertas Pendientes*\n\n"
    for o in ofertas:
        text += f"*{o['titulo']}* ({o['score']}/10)\n{o['empresa']}\n{o['url']}\n\n"
    return text


# --- /stats ---

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _get_user(update)
    if not user:
        await update.message.reply_text("Usa /setup para registrarte primero.")
        return
    stats = get_user_stats(user['id'])
    text = (
        f"*Estadisticas de {user['username']}*\n\n"
        f"Total vistas: {stats['total_vistas']}\n"
        f"Aplicadas: {stats['total_aplicadas']}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# --- Inline buttons ---

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = get_user_by_chat_id(query.from_user.id)
    if not user:
        await query.edit_message_text("Usa /setup para registrarte.")
        return

    if query.data == "pendientes":
        await query.edit_message_text(_pendientes_text(user['id']), parse_mode="Markdown")
    elif query.data == "stats":
        stats = get_user_stats(user['id'])
        text = (
            f"*Estadisticas de {user['username']}*\n\n"
            f"Total vistas: {stats['total_vistas']}\n"
            f"Aplicadas: {stats['total_aplicadas']}"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
    elif query.data == "help":
        await query.edit_message_text(
            "*Ayuda*\n\n"
            "/start - Menu principal\n"
            "/pendientes - Ver ofertas\n"
            "/stats - Estadisticas\n"
            "/config - Editar sueldo, stack, ubicacion\n"
            "/setup - Registro inicial",
            parse_mode="Markdown"
        )


# --- Bot startup ---

def start_bot(token):
    init_db()
    application = Application.builder().token(token).build()

    setup_conv = ConversationHandler(
        entry_points=[CommandHandler("setup", setup_start)],
        states={
            SETUP_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_username)],
            SETUP_SUELDO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_sueldo)],
            SETUP_STACK:    [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_stack)],
            SETUP_UBICACION:[MessageHandler(filters.TEXT & ~filters.COMMAND, setup_ubicacion)],
            SETUP_EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_email)],
        },
        fallbacks=[CommandHandler("cancel", setup_cancel)]
    )

    config_conv = ConversationHandler(
        entry_points=[CommandHandler("config", config_start)],
        states={
            CONFIG_FIELD: [CallbackQueryHandler(config_field, pattern="^cfg_")],
            CONFIG_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, config_value)],
        },
        fallbacks=[CommandHandler("cancel", config_cancel)],
        per_message=False,
    )

    application.add_handler(setup_conv)
    application.add_handler(config_conv)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pendientes", pendientes_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()


def main():
    parser = argparse.ArgumentParser(description='Job Agent Telegram Bot')
    parser.add_argument('--user', required=True, help='Username whose bot token to use')
    args = parser.parse_args()

    config = load_user_config(args.user)
    token = config.get('TELEGRAM_BOT_TOKEN')
    if not token:
        print(f"[!] TELEGRAM_BOT_TOKEN no encontrado para el usuario '{args.user}'")
        return

    print(f"[*] Iniciando bot para usuario: {args.user}")
    start_bot(token)


if __name__ == "__main__":
    main()
