from telegram import Update

async def phrase_middleware(update: Update, context):
    text = update.message.text if update.message and update.message.text else ""
    if "cine" in text.lower():
        await update.message.reply_text("🎥 ¡Viva el buen cine!")
