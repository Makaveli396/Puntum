from telegram import Update
from telegram.ext import ContextTypes

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🎬 *Bienvenido a Puntum Bot: cinefilia sin censura* 🎬\n\n"
        "Aquí no hay espacio para el aburrimiento. Este bot es tu asistente en la jungla del cine, "
        "donde cada aporte cuenta y cada reseña deja huella.\n\n"
        "*Comandos disponibles:*\n"
        "▪️ `/start` — Despierta al bot, como si abrieras el telón.\n"
        "▪️ `/help` — Estás aquí. ¿Qué más quieres?\n"
        "▪️ `/ranking` — Top 10 cinéfilos. Solo los duros sobreviven.\n"
        "▪️ `/reto` — El desafío de la semana. ¿Tienes agallas?\n"
        "▪️ `/mipuntaje` — Muestra tus stats. Eres el protagonista o un extra más.\n\n"
        "*¿Cómo ganar puntos?*\n"
        "Usa hashtags al estilo salvaje:\n"
        "🔸 `#aporte` — 3 pts: Comparte links o joyas ocultas.\n"
        "🔸 `#recomendación` — 5 pts: Que no se te escape ese peliculón.\n"
        "🔸 `#reseña` — 7 pts: Escribe como si fueras Scorsese.\n"
        "🔸 `#crítica` — 10 pts: A lo Tarantino, sin filtros.\n"
        "🔸 `#pregunta`, `#spoiler`, `#debate` — Más puntos si prendes fuego al grupo.\n\n"
        "*Frases gatillo:*\n"
        "¿Dijiste 'cine'? Entonces prepárate, porque el bot responde. Como en un buen guion, "
        "las palabras importan.\n\n"
        "_Puntum Bot no es solo un bot. Es una experiencia Tarantinesca._ 💥"
    )
    await update.message.reply_markdown_v2(mensaje)
