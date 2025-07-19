from telegram import Update
from db import get_current_challenge, set_challenge, add_points
import random
import datetime

# Pool de retos cinematográficos
WEEKLY_CHALLENGES = [
    {
        "title": "🎭 Semana del Cine Clásico",
        "description": "Comparte una reseña de una película anterior a 1980",
        "hashtag": "#reseña",
        "bonus_points": 5,
        "validation": lambda text: any(year in text for year in [str(y) for y in range(1900, 1980)])
    },
    {
        "title": "🌍 Semana del Cine Internacional", 
        "description": "Recomienda una película no estadounidense con formato completo",
        "hashtag": "#recomendación",
        "bonus_points": 7,
        "validation": lambda text: True  # Se valida por formato en hashtags.py
    },
    {
        "title": "🎪 Semana del Cine de Culto",
        "description": "Haz una crítica de una película considerada 'de culto'",
        "hashtag": "#crítica", 
        "bonus_points": 10,
        "validation": lambda text: any(word in text.lower() for word in ['culto', 'underground', 'indie', 'alternativo'])
    },
    {
        "title": "🏆 Semana de Directores Legendarios",
        "description": "Aporta contenido sobre Kubrick, Tarantino, Scorsese, Coppola o Hitchcock",
        "hashtag": "#aporte",
        "bonus_points": 6,
        "validation": lambda text: any(director in text.lower() for director in ['kubrick', 'tarantino', 'scorsese', 'coppola', 'hitchcock'])
    },
    {
        "title": "🎨 Semana del Análisis Profundo",
        "description": "Inicia un debate sobre técnicas cinematográficas (fotografía, sonido, montaje)",
        "hashtag": "#debate",
        "bonus_points": 8,
        "validation": lambda text: any(word in text.lower() for word in ['fotografía', 'sonido', 'montaje', 'edición', 'cinematografía', 'plano'])
    },
    {
        "title": "🔍 Semana del Cine Perdido",
        "description": "Pregunta por películas difíciles de encontrar o poco conocidas",
        "hashtag": "#pregunta",
        "bonus_points": 4,
        "validation": lambda text: any(word in text.lower() for word in ['dónde ver', 'conocen', 'recomiendan', 'perdida', 'rara'])
    }
]

async def cmd_reto(update: Update, context):
    """Comando para mostrar el reto actual de la semana"""
    try:
        current_challenge = get_current_challenge()
        
        if current_challenge:
            msg = f"🎯 **RETO DE LA SEMANA**\n\n"
            msg += f"**{current_challenge['title']}**\n\n"
            msg += f"📝 {current_challenge['description']}\n\n"
            msg += f"🏷️ Usa: {current_challenge['hashtag']}\n"
            msg += f"🎁 Bonus: +{current_challenge['bonus_points']} puntos extra\n\n"
            msg += f"⏰ Válido hasta: {get_next_sunday()}\n\n"
            msg += "💡 *Tip: Los retos se renuevan cada domingo*"
        else:
            msg = "🔄 Generando nuevo reto. Usa `/reto` en unos minutos."
            
        await update.message.reply_text(msg)
        
    except Exception as e:
        print(f"[ERROR] en cmd_reto: {e}")
        await update.message.reply_text("⚠️ Error al obtener reto. Intenta en unos minutos.")

async def reto_job(context):
    """Job que se ejecuta cada domingo para generar nuevo reto semanal"""
    try:
        print("[DEBUG] Ejecutando reto_job semanal")
        
        # Seleccionar reto aleatorio
        new_challenge = random.choice(WEEKLY_CHALLENGES)
        
        # Guardar en BD (necesitaremos actualizar db.py)
        set_challenge(new_challenge)
        
        # Notificar al grupo si tenemos chat_id
        chat_id = context.job.data if context.job.data else None
        if chat_id:
            msg = f"🚨 **¡NUEVO RETO SEMANAL!**\n\n"
            msg += f"**{new_challenge['title']}**\n\n" 
            msg += f"🎯 {new_challenge['description']}\n\n"
            msg += f"🏷️ Usa: {new_challenge['hashtag']}\n"
            msg += f"🎁 Bonus: +{new_challenge['bonus_points']} puntos extra\n\n"
            msg += "⚡ ¡El que participe primero se lleva puntos adicionales!"
            
            await context.bot.send_message(chat_id=chat_id, text=msg)
            
        print(f"[DEBUG] Nuevo reto configurado: {new_challenge['title']}")
        
    except Exception as e:
        print(f"[ERROR] en reto_job: {e}")

async def check_challenge_completion(update: Update, context, hashtag, text):
    """Verifica si un mensaje cumple con el reto actual"""
    try:
        current_challenge = get_current_challenge()
        
        if not current_challenge:
            return 0
            
        # Verificar si el hashtag coincide
        if hashtag != current_challenge.get('hashtag'):
            return 0
            
        # Verificar validación específica del reto
        validation_func = current_challenge.get('validation')
        if validation_func and validation_func(text):
            bonus_points = current_challenge.get('bonus_points', 0)
            
            # Notificar al usuario
            await update.message.reply_text(
                f"🎯 ¡RETO COMPLETADO!\n"
                f"Bonus: +{bonus_points} puntos por '{current_challenge['title']}'"
            )
            
            return bonus_points
            
        return 0
        
    except Exception as e:
        print(f"[ERROR] verificando reto: {e}")
        return 0

def get_next_sunday():
    """Obtiene la fecha del próximo domingo"""
    today = datetime.date.today()
    days_ahead = 6 - today.weekday()  # Domingo es 6
    if days_ahead <= 0:  # Si hoy es domingo
        days_ahead += 7
    next_sunday = today + datetime.timedelta(days_ahead)
    return next_sunday.strftime("%d/%m/%Y")

def get_current_challenge():
    """Obtiene el reto actual - implementación temporal hasta actualizar DB"""
    # Por ahora devuelve un reto aleatorio
    # TODO: Implementar correctamente con BD
    import json
    try:
        # Intentar leer desde archivo temporal
        with open('current_challenge.json', 'r') as f:
            return json.load(f)
    except:
        # Si no existe, crear uno nuevo
        challenge = random.choice(WEEKLY_CHALLENGES)
        try:
            with open('current_challenge.json', 'w') as f:
                json.dump(challenge, f)
        except:
            pass
        return challenge
