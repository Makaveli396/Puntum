from db import get_top10
from telegram import Update
import datetime
import random

# Frases cinematográficas para el ranking
RANKING_PHRASES = [
    "🥇 {winner} se lleva la Palma de Oro esta semana",
    "🎬 {winner} protagoniza este ranking como si fuera Marlon Brando",
    "🏆 {winner} domina la cartelera con {points} puntos",
    "⭐ {winner} brilla más que las luces de Hollywood",
    "🎭 {winner} actúa como si fuera el último día en Cannes"
]

CLOSING_PHRASES = [
    "📽️ ¡Que el show continúe la próxima semana!",
    "🎞️ El séptimo arte nunca descansa...",
    "🎪 ¡Lights, camera, action para una nueva semana!",
    "🎨 El cine es pasión, y ustedes lo demuestran cada día",
    "🎯 Próximo capítulo: domingo que viene, misma hora"
]

async def cmd_ranking(update: Update, context):
    """Comando manual para mostrar ranking actual"""
    top = get_top10()
    if not top:
        await update.message.reply_text("📝 Aún no hay participantes. ¡Sé el primero en usar hashtags!")
        return
    
    msg = "🎬 **TOP 10 CINÉFILOS ACTUALES**\n\n"
    
    for i, (user, pts) in enumerate(top, 1):
        if i == 1:
            msg += f"🥇 {user} - {pts} pts\n"
        elif i == 2:
            msg += f"🥈 {user} - {pts} pts\n"
        elif i == 3:
            msg += f"🥉 {user} - {pts} pts\n"
        else:
            msg += f"🎭 {i}. {user} - {pts} pts\n"
    
    msg += f"\n📅 Próximo ranking oficial: {get_next_sunday()}"
    await update.message.reply_text(msg)

async def ranking_job(context):
    """Job que se ejecuta automáticamente cada domingo a las 20:00"""
    try:
        print("[DEBUG] Ejecutando ranking_job semanal")
        
        # Obtener chat_id desde job_data o usar un grupo predeterminado
        chat_id = context.job.data if context.job.data else None
        if not chat_id:
            print("[WARNING] No hay chat_id configurado para ranking automático")
            return
        
        top = get_top10()
        if not top:
            await context.bot.send_message(
                chat_id=chat_id,
                text="📝 Esta semana no hubo participación. ¡Anímense con los hashtags!"
            )
            return
        
        # Crear mensaje épico del ranking
        winner = top[0][0]  # Primer lugar
        winner_points = top[0][1]
        
        # Frase aleatoria para el ganador
        winner_phrase = random.choice(RANKING_PHRASES).format(
            winner=winner, 
            points=winner_points
        )
        
        msg = f"🎬 **RANKING SEMANAL OFICIAL**\n"
        msg += f"📅 Semana del {get_last_week_range()}\n\n"
        msg += f"{winner_phrase}\n\n"
        msg += "🏆 **TOP 10 DE LA SEMANA:**\n\n"
        
        for i, (user, pts) in enumerate(top, 1):
            if i == 1:
                msg += f"🥇 {user} - {pts} pts\n"
            elif i == 2:
                msg += f"🥈 {user} - {pts} pts\n"
            elif i == 3:
                msg += f"🥉 {user} - {pts} pts\n"
            else:
                msg += f"🎭 {i}. {user} - {pts} pts\n"
        
        msg += f"\n{random.choice(CLOSING_PHRASES)}"
        
        await context.bot.send_message(chat_id=chat_id, text=msg)
        
        # Opcional: Reset de puntos semanales (descomentar si quieres ranking semanal real)
        # reset_weekly_points()
        
    except Exception as e:
        print(f"[ERROR] en ranking_job: {e}")

def get_next_sunday():
    """Obtiene la fecha del próximo domingo"""
    today = datetime.date.today()
    days_ahead = 6 - today.weekday()  # Domingo es 6
    if days_ahead <= 0:  # Si hoy es domingo
        days_ahead += 7
    next_sunday = today + datetime.timedelta(days_ahead)
    return next_sunday.strftime("%d/%m/%Y")

def get_last_week_range():
    """Obtiene el rango de la semana pasada"""
    today = datetime.date.today()
    last_sunday = today - datetime.timedelta(days=today.weekday() + 1)
    last_saturday = last_sunday + datetime.timedelta(days=6)
    return f"{last_sunday.strftime('%d/%m')} - {last_saturday.strftime('%d/%m')}"

def reset_weekly_points():
    """Reinicia puntos semanales (opcional - usar solo si quieres ranking semanal real)"""
    from db import conn, cur
    try:
        cur.execute("UPDATE users SET points = 0")
        conn.commit()
        print("[DEBUG] Puntos semanales reiniciados")
    except Exception as e:
        print(f"[ERROR] al reiniciar puntos: {e}")
