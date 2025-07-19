from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import os, json

RETO_SEMANAL = {
    "hashtag": "#crítica",
    "min_words": 100,
    "bonus_points": 15
}

def get_current_challenge():
    if os.path.exists("custom_challenge.txt"):
        with open("custom_challenge.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def set_challenge(text):
    with open("custom_challenge.txt", "w", encoding="utf-8") as f:
        f.write(text.strip())

def clear_challenge():
    if os.path.exists("custom_challenge.txt"):
        os.remove("custom_challenge.txt")

def get_weekly_challenge():
    return RETO_SEMANAL

def validate_challenge_submission(challenge, text):
    hashtag_ok = challenge["hashtag"] in text.lower()
    word_count = len(text.split())
    if hashtag_ok and word_count >= challenge.get("min_words", 0):
        return True
    return False

# NUEVOS: comandos y tarea programada

async def cmd_reto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reto = get_weekly_challenge()
    text = (
        f"🎬 *Reto semanal activo:*
"
        f"Hashtag: `{reto['hashtag']}`
"
        f"Requiere mínimo *{reto['min_words']}* palabras.
"
        f"Bonus: +{reto['bonus_points']} puntos"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_nuevo_reto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /nuevoreto <hashtag> <min_palabras> <bonus>")
        return

    try:
        hashtag = context.args[0]
        min_words = int(context.args[1])
        bonus = int(context.args[2])

        global RETO_SEMANAL
        RETO_SEMANAL = {
            "hashtag": hashtag,
            "min_words": min_words,
            "bonus_points": bonus
        }

        await update.message.reply_text(f"✅ Nuevo reto semanal activado: {hashtag}, {min_words} palabras, +{bonus} pts")

    except ValueError:
        await update.message.reply_text("❌ Error en los parámetros. Usa números para min_palabras y bonus.")

async def reto_job(context: ContextTypes.DEFAULT_TYPE):
    reto = get_weekly_challenge()
    text = (
        f"📢 *Reto semanal actual:*
"
        f"Hashtag: `{reto['hashtag']}`
"
        f"Requiere mínimo *{reto['min_words']}* palabras.
"
        f"Bonus: +{reto['bonus_points']} puntos"
    )
    await context.bot.send_message(chat_id=context.job.chat_id, text=text, parse_mode="Markdown")