from telegram import Update
from telegram.ext import ContextTypes
from db import get_current_challenge, set_challenge, clear_challenge
from datetime import datetime

# Retos predefinidos con validaciones string-based
WEEKLY_CHALLENGES = [
    {
        "id": 1,
        "title": "Documental Latinoamericano",
        "description": "Recomienda un documental latinoamericano anterior al año 2000",
        "hashtag": "#recomendación",
        "bonus_points": 10,
        "validation_keywords": ["argentina", "méxico", "brasil", "chile", "colombia", "perú", "venezuela", "bolivia", "ecuador"],
        "validation_type": "country_keywords"
    },
    {
        "id": 2,
        "title": "Cine de Terror Clásico",
        "description": "Reseña una película de terror de los años 70-80",
        "hashtag": "#reseña",
        "bonus_points": 15,
        "validation_keywords": ["70", "80", "1970", "1980", "terror", "horror"],
        "validation_type": "genre_keywords"
    },
]

def get_weekly_challenge():
    # Devuelve el reto predefinido en función de la semana actual
    week_number = datetime.now().isocalendar()[1]
    return WEEKLY_CHALLENGES[week_number % len(WEEKLY_CHALLENGES)]

def validate_challenge_submission(challenge, message_text):
    message_text = message_text.lower()
    if challenge.get("validation_type") == "country_keywords":
        return any(keyword in message_text for keyword in challenge["validation_keywords"])
    elif challenge.get("validation_type") == "genre_keywords":
        return any(keyword in message_text for keyword in challenge["validation_keywords"])
    return False

async def cmd_reto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reto = get_weekly_challenge()
    text = (
        f"📢 *Reto semanal actual:*\n"
        f"*Título:* {reto['title']}\n"
        f"*Descripción:* {reto['description']}\n"
        f"*Hashtag:* `{reto['hashtag']}`\n"
        f"*Bonus:* +{reto['bonus_points']} puntos"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_nuevo_reto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_challenge("")
    await update.message.reply_text("✅ El reto personalizado ha sido limpiado. Se usará el reto automático.")

async def cmd_borrar_reto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_challenge()
    await update.message.reply_text("🗑️ Reto semanal personalizado eliminado.")
