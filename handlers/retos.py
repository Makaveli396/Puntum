from telegram import Update

def cmd_reto(update: Update, context):
    update.message.reply_text("📌 Nuevo reto próximamente...")

def reto_job(context): pass
