from db import get_user_stats, get_level_info
from telegram import Update
from telegram.ext import ContextTypes

async def cmd_mipuntaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para mostrar estadísticas detalladas del usuario"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuario"
        
        # Obtener estadísticas del usuario
        stats = get_user_stats(user_id)
        
        if not stats:
            msg = (
                "🎬 ¡Bienvenido al CineBot!\n\n"
                "Aún no tienes puntos. ¡Empieza a participar con hashtags de películas!\n\n"
                "📝 Ejemplos: #StarWars #Inception #Titanic\n"
                "💡 Usa /help para más información"
            )
            await update.message.reply_text(msg)
            return
        
        # Construir mensaje con estadísticas completas
        msg = f"🎯 **{stats['username']}**\n"
        msg += f"━━━━━━━━━━━━━━━━━━\n"
        msg += f"🏆 **Puntos:** {stats['points']}\n"
        msg += f"📝 **Aportes:** {stats['count']}\n"
        msg += f"🎖️ **Nivel:** {stats['level']} - {stats['level_name']}\n"
        
        # Mostrar progreso al siguiente nivel si no está en el máximo
        if stats['points_to_next'] > 0:
            msg += f"⬆️ **Siguiente nivel:** {stats['points_to_next']} puntos más\n"
        else:
            msg += f"👑 **¡Nivel máximo alcanzado!**\n"
        
        msg += f"━━━━━━━━━━━━━━━━━━\n"
        
        # Mostrar contribuciones recientes si existen
        if stats.get('recent_contributions'):
            msg += f"📋 **Últimas contribuciones:**\n"
            for contrib in stats['recent_contributions'][:3]:  # Solo las últimas 3
                hashtag = contrib[0] if contrib[0] else "general"
                points = contrib[1]
                msg += f"   • {hashtag} (+{points} pts)\n"
        
        # Información adicional
        if stats.get('member_since'):
            from datetime import datetime
            try:
                member_since = datetime.fromisoformat(stats['member_since'].replace('Z', '+00:00'))
                days_active = (datetime.now() - member_since).days
                if days_active > 0:
                    msg += f"\n🗓️ **Miembro desde hace:** {days_active} días"
            except:
                pass  # Si hay error con la fecha, simplemente no la mostramos
        
        msg += f"\n\n💡 Usa /ranking para ver el top 10"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        print(f"[ERROR] Error en cmd_mipuntaje: {e}")
        await update.message.reply_text(
            "❌ Hubo un error al obtener tus estadísticas. "
            "Inténtalo de nuevo en unos momentos."
        )

async def cmd_miperfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando alternativo más detallado para mostrar el perfil completo"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuario"
        
        stats = get_user_stats(user_id)
        
        if not stats:
            await cmd_mipuntaje(update, context)  # Redirigir al comando básico
            return
        
        # Mensaje más detallado
        msg = f"👤 **PERFIL DE {stats['username'].upper()}**\n"
        msg += f"{'━' * 25}\n\n"
        
        # Estadísticas principales
        msg += f"🏆 **Puntos totales:** {stats['points']}\n"
        msg += f"📝 **Contribuciones:** {stats['count']}\n"
        msg += f"🎖️ **Nivel actual:** {stats['level']}\n"
        msg += f"👑 **Título:** {stats['level_name']}\n\n"
        
        # Progreso de nivel
        if stats['points_to_next'] > 0:
            level_info = get_level_info(stats['level'])
            if level_info and level_info.get('next_points'):
                current_level_points = stats['points'] - level_info['min_points']
                next_level_points = level_info['next_points'] - level_info['min_points']
                progress_percentage = (current_level_points / next_level_points) * 100 if next_level_points > 0 else 100
                
                progress_bar = create_progress_bar(progress_percentage)
                msg += f"📊 **Progreso al nivel {stats['level'] + 1}:**\n"
                msg += f"{progress_bar} {progress_percentage:.1f}%\n"
                msg += f"Faltan {stats['points_to_next']} puntos\n\n"
        
        # Actividad reciente
        if stats.get('recent_contributions'):
            msg += f"🎬 **Actividad reciente:**\n"
            for i, contrib in enumerate(stats['recent_contributions'][:5], 1):
                hashtag = contrib[0] if contrib[0] else "general"
                points = contrib[1]
                msg += f"{i}. {hashtag} (+{points} pts)\n"
        
        # Estadísticas adicionales
        if stats['count'] > 0:
            avg_points = stats['points'] / stats['count']
            msg += f"\n📈 **Promedio por aporte:** {avg_points:.1f} pts\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        print(f"[ERROR] Error en cmd_miperfil: {e}")
        await cmd_mipuntaje(update, context)  # Fallback al comando básico

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Crea una barra de progreso visual"""
    filled = int((percentage / 100) * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"

# Función auxiliar para formatear números grandes
def format_number(num: int) -> str:
    """Formatea números para hacerlos más legibles"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

# Funciones para obtener estadísticas comparativas
async def get_user_rank(user_id: int) -> int:
    """Obtiene la posición del usuario en el ranking global"""
    try:
        from db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) + 1 as rank
            FROM (
                SELECT user_id, SUM(points) as total_points
                FROM points
                GROUP BY user_id
            ) u1
            WHERE u1.total_points > (
                SELECT COALESCE(SUM(points), 0) FROM points WHERE user_id = ?
            )
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"[ERROR] Error obteniendo rank: {e}")
        return 0

async def cmd_mirank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para mostrar solo la posición en el ranking"""
    try:
        user_id = update.effective_user.id
        stats = get_user_stats(user_id)
        
        if not stats:
            await update.message.reply_text("❌ Necesitas tener puntos para ver tu ranking.")
            return
        
        rank = await get_user_rank(user_id)
        
        msg = f"🏆 **{stats['username']}**\n"
        msg += f"📊 Posición en ranking: **#{rank}**\n"
        msg += f"🎯 Puntos: **{stats['points']}**\n"
        msg += f"🎖️ Nivel: **{stats['level']} - {stats['level_name']}**"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        print(f"[ERROR] Error en cmd_mirank: {e}")
        await update.message.reply_text("❌ Error al obtener tu posición en el ranking.")
