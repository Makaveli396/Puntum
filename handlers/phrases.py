from telegram import Update

async def phrase_middleware(update: Update, context):
    # Solo procesar si hay mensaje y texto
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    print(f"[DEBUG] Mensaje recibido: {update.message.text}")
    
    # Solo responder si contiene "cine"
    if "cine" in text:
        await update.message.reply_text("🎥 ¡Viva el buen cine!")
