from telegram import Update

def phrase_middleware(update: Update, context):
    if "cine" in update.message.text.lower():
        update.message.reply_text("🎥 ¡Viva el buen cine!")
