from telegram import Update

async def phrase_middleware(update: Update, context):
    if update.message:
        print(f"[DEBUG] Mensaje recibido: {update.message.text}")
        await update.message.reply_text("📨 Mensaje recibido")

    text = update.message.text if update.message and update.message.text else ""
    if "cine" in text.lower():
        await update.message.reply_text("🎥 ¡Viva el buen cine!")
