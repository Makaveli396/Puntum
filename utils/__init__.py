
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_points, get_user_level, get_user_stats

async def cmd_mipuntaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    points = get_user_points(user_id)
    level = get_user_level(points)

    await update.message.reply_text(
        f"🎟️ {username}, tienes {points} puntos.\n"
        f"🌟 Nivel actual: {level}"
    )

async def cmd_miperfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)

    if not stats:
        await update.message.reply_text("❌ No tienes actividad registrada.")
        return

    await update.message.reply_text(
        f"🎭 Perfil de {update.effective_user.first_name}:\n"
        f"- Puntos: {stats['points']}\n"
        f"- Nivel: {stats['level']}\n"
        f"- Hashtags usados: {stats['hashtags']}\n"
        f"- Días activo: {stats['active_days']}"
    )

async def cmd_mirank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rank = get_user_stats(user_id).get("rank", "No disponible")

    await update.message.reply_text(
        f"📈 Estás en la posición #{rank} del ranking."
    )
