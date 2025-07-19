from telegram import Update
from telegram.ext import ContextTypes
from db import get_current_challenge, set_challenge, clear_challenge
import os
from datetime import datetime

# Retos predefinidos con validaciones string-based
WEEKLY_CHALLENGES = [
    {
        "id": 1,
        "title": "Documental Latinoamericano",
        "description": "Recomienda un documental latinoamericano anterior al año 2000",
        "hashtag": "#recomendación",
        "bonus_points": 10,
        "validation_keywords": ["argentina", "méxico", "brasil", "chile", "colombia", "perú", "venezuela", "bolivia", "ecuador", "uruguay", "paraguay"],
        "validation_type": "country_keywords"
    },
    {
        "id": 2,
        "title": "Cine de Terror Clásico",
        "description": "Reseña una película de terror de los años 70-80",
        "hashtag": "#reseña",
        "bonus_points": 15,
        "validation_keywords": ["70", "80", "1970", "1980", "terror", "horror"],
        "validation_type": "decade_genre"
    },
    {
        "id": 3,
        "title": "Director Europeo",
        "description": "Crítica de una película de directores europeos icónicos",
        "hashtag": "#crítica",
        "bonus_points": 12,
        "validation_keywords": ["bergman", "fellini", "tarkovsky", "godard", "truffaut", "antonioni", "buñuel"],
        "validation_type": "director_keywords"
    },
    {
        "id": 4,
        "title": "Cine Independiente",
        "description": "Aporta información sobre cine independiente o bajo presupuesto",
        "hashtag": "#aporte",
        "bonus_points": 8,
        "validation_keywords": ["independiente", "indie", "bajo presupuesto", "experimental"],
        "validation_type": "genre_keywords"
    }
]

def get_weekly_challenge():
    """Obtiene el reto de la semana basado en número de semana del año"""
    week_number = datetime.now().isocalendar()[1]
    challenge_index = (week_number - 1) % len(WEEKLY_CHALLENGES)
    return WEEKLY_CHALLENGES[challenge_index]

def validate_challenge_submission(challenge, text):
    """Valida si un mensaje cumple con los requisitos del reto"""
    text_lower = text.lower()
    
    if challenge["validation_type"] == "country_keywords":
        return any(keyword in text_lower for keyword in challenge["validation_keywords"])
    
    elif challenge["validation_type"] == "decade_genre":
        has_decade = any(decade in text_lower for decade in ["70", "80", "1970", "1980"])
        has_genre = any(genre in text_lower for genre in ["terror", "horror"])
        return has_decade or has_genre
    
    elif challenge["validation_type"] == "director_keywords":
        return any(director in text_lower for director in challenge["validation_keywords"])
    
    elif challenge["validation_type"] == "genre_keywords":
        return any(keyword in text_lower for keyword in challenge["validation_keywords"])
    
    return False

async def cmd_reto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el reto actual de la semana"""
    try:
        # Intentar obtener reto personalizado de la DB
        current_challenge = get_current_challenge()
        
        if current_challenge:
            # Reto personalizado desde DB
            mensaje = (
                f"🎯 **Reto Especial**\n\n"
                f"📽️ {current_challenge}\n\n"
                f"💰 **Recompensa**: Puntos adicionales según hashtag utilizado\n"
                f"⏰ **Válido**: Hasta que se establezca un nuevo reto\n\n"
                f"¡Participa y demuestra tu conocimiento cinéfilo!"
            )
        else:
            # Reto automático semanal
            challenge = get_weekly_challenge()
            mensaje = (
                f"🎯 **Reto de la Semana #{datetime.now().isocalendar()[1]}**\n\n"
                f"📽️ **{challenge['title']}**\n"
                f"{challenge['description']}\n\n"
                f"💰 **Recompensa**: +{challenge['bonus_points']} puntos adicionales\n"
                f"🏷️ **Usa el hashtag**: {challenge['hashtag']}\n"
                f"⏰ **Válido hasta**: Próximo lunes\n\n"
                f"💡 *Tip: El bot validará automáticamente tu participación*"
            )
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
        
    except Exception as e:
        print(f"[ERROR] Error en cmd_reto: {e}")
        await update.message.reply_text("❌ Error al obtener el reto actual. Inténtalo más tarde.")

async def reto_job(context):
    """Job que se ejecuta semanalmente para anunciar el nuevo reto"""
    try:
        # Obtener chat_id desde job_data
        chat_id = context.job.data if hasattr(context.job, 'data') and context.job.data else None
        
        if not chat_id:
            print("[ERROR] No hay chat_id configurado para reto automático")
            return
        
        # Obtener reto de la semana
        challenge = get_weekly_challenge()
        
        mensaje = (
            f"🚨 **¡NUEVO RETO SEMANAL!** 🚨\n\n"
            f"📽️ **{challenge['title']}**\n"
            f"{challenge['description']}\n\n"
            f"💰 **Recompensa**: +{challenge['bonus_points']} puntos adicionales\n"
            f"🏷️ **Hashtag requerido**: {challenge['hashtag']}\n"
            f"⏰ **Plazo**: 7 días desde ahora\n\n"
            f"¡A demostrar sus conocimientos cinéfilos! 🎬\n"
            f"Usa `/reto` para ver los detalles cuando quieras."
        )
        
        # Enviar al chat configurado
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=mensaje,
                parse_mode='Markdown'
            )
            print(f"[INFO] Reto semanal enviado a chat {chat_id}")
        except Exception as e:
            print(f"[ERROR] No se pudo enviar reto a chat {chat_id}: {e}")
                
    except Exception as e:
        print(f"[ERROR] Error en reto_job: {e}")

async def cmd_nuevo_reto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para que administradores establezcan retos personalizados"""
    # IDs de administradores desde variables de entorno
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    
    if not ADMIN_IDS or update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Solo administradores pueden usar este comando")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **Uso:** `/nuevoreto <descripción del reto>`\n\n"
            "**Ejemplo:**\n"
            "`/nuevoreto Recomienda una película de Akira Kurosawa`\n\n"
            "**Para limpiar reto actual:**\n"
            "`/nuevoreto limpiar`",
            parse_mode='Markdown'
        )
        return
    
    reto_text = " ".join(context.args)
    
    # Comando especial para limpiar
    if reto_text.lower() == "limpiar":
        try:
            clear_challenge()
            await update.message.reply_text("✅ **Reto personalizado eliminado**\nAhora se usarán los retos semanales automáticos")
            return
        except Exception as e:
            print(f"[ERROR] Error limpiando reto: {e}")
            await update.message.reply_text("❌ Error al limpiar el reto")
            return
    
    try:
        set_challenge(reto_text)
        await update.message.reply_text(
            f"✅ **Nuevo reto establecido:**\n\n"
            f"📽️ {reto_text}\n\n"
            f"Los usuarios pueden verlo con `/reto`",
            parse_mode='Markdown'
        )
        
        print(f"[INFO] Reto personalizado establecido por admin {update.effective_user.id}")
        
    except Exception as e:
        print(f"[ERROR] Error en cmd_nuevo_reto: {e}")
        await update.message.reply_text("❌ Error al establecer el reto")
