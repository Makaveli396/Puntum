from telegram import Update

async def cmd_reto(update: Update, context):
    await update.message.reply_text("📌 Nuevo reto próximamente...")

async def reto_job(context): pass
