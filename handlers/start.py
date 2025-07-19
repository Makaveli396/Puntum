from telegram import Update
from telegram.ext import ContextTypes

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🎬 *¡Acción\\!*\\n\\n"
        "Bienvenido a *Puntum Bot*, tu cómplice en la locura cinéfila\\. Aquí no venimos a ver trailers: "
        "esto es la película completa\\.\n\n"
        "Envía `/help` para conocer cómo participar, ganar puntos y dominar la conversación de cine "
        "como si fueras Tarantino escribiendo un guión con Kubrick\\.\n\n"
        "📽️ ¡Luces, cámara\\.\\.\\. interacción\\!"
    )
    await update.message.reply_markdown_v2(mensaje)

