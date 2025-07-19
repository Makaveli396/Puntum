from telegram import Update

def spam_handler(update: Update, context):
    if "gratis" in update.message.text.lower():
        update.message.reply_text("🛑 ¡Cuidado con el spam!")
