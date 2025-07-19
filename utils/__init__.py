from db import get_user_stats
from telegram import Update

def cmd_mipuntaje(update: Update, context):
    stats = get_user_stats(update.effective_user.id)
    if stats:
        msg = f"🎯 {stats['username']}\nPuntos: {stats['points']}\nAportes: {stats['count']}"
    else:
        msg = "No tienes puntos todavía."
    update.message.reply_text(msg)
