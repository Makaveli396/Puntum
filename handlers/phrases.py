from telegram import Update

async def phrase_middleware(update: Update, context):
    if "cine" in update.message.text.lower():
        await update.message.reply_text("🎥 ¡Viva el buen cine!")
