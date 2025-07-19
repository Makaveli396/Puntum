from telegram import Update
from db import get_current_challenge, set_challenge
import random
import datetime
import re

# Pool de retos cinematográficos con validaciones serializables
WEEKLY_CHALLENGES = [
    {
        "title": "🎭 Semana del Cine Clásico",
        "description": "Comparte una reseña de una película anterior a 1980",
        "hashtag": "#reseña",
        "bonus_points": 5,
        "validation_type": "year_range",
        "validation_params": {"min_year": 1900, "max_year": 1979}
    },
    {
        "title": "🌍 Semana del Cine Internacional", 
        "description": "Recomienda una película no estadounidense con formato completo",
        "hashtag": "#recomendación",
        "bonus_points": 7,
        "validation_type": "format_check",
        "validation_params": {"requires_format": True}
    },
    {
        "title": "🎪 Semana del Cine de Culto",
        "description": "Haz una crítica de una película considerada 'de culto'",
        "hashtag": "#crítica", 
        "bonus_points": 10,
        "validation_type": "keyword_match",
        "validation_params": {"keywords": ["culto", "underground", "indie", "alternativo", "b movie", "exploitation"]}
    },
    {
        "title": "🏆 Semana de Directores Legendarios",
        "description": "Aporta contenido sobre Kubrick, Tarantino, Scorsese, Coppola o Hitchcock",
        "hashtag": "#aporte",
        "bonus_points": 6,
        "validation_type": "keyword_match",
        "validation_params": {"keywords": ["kubrick", "tarantino", "scorsese", "coppola", "hitchcock", "bergman", "fellini"]}
    },
    {
        "title": "🎨 Semana del Análisis Profundo",
        "description": "Inicia un debate sobre técnicas cinematográficas",
        "hashtag": "#debate",
        "bonus_points": 8,
        "validation_type": "keyword_match",
        "validation_params": {"keywords": ["fotografía", "sonido", "montaje", "edición", "cinematografía", "plano", "iluminación", "banda sonora"]}
    },
    {
        "title": "🔍 Semana del Cine Perdido",
        "description": "Pregunta por películas difíciles de encontrar o poco conocidas",
        "hashtag": "#pregunta",
        "bonus_points": 4,
        "validation_type": "keyword_match",
        "validation_params": {"keywords": ["dónde ver", "conocen", "recomiendan", "perdida", "rara", "difícil encontrar", "descatalogada"]}
    },
    {
        "title": "🎞️ Semana de Documentales",
        "description": "Comparte una reseña o recomendación de documental",
        "hashtag": "#reseña",
        "bonus_points": 6,
        "validation_type": "keyword_match", 
        "validation_params": {"keywords": ["documental", "documentary", "no ficción", "real", "testimonio"]}
    },
    {
        "title": "🏴‍☠️ Semana del Cine Pirata",
        "description": "Habla sobre cine independiente o producciones guerrilla",
        "hashtag": "#crítica",
        "bonus_points": 7,
        "validation_type": "keyword_match",
        "validation_params": {"keywords": ["independiente", "guerrilla", "low budget", "mumblecore", "dogma 95"]}
    }
]

def validate_challenge_text(text, validation_type, validation_params):
    """Valida si un texto cumple con los criterios del reto"""
    text_lower = text.lower()
    
    if validation_type == "year_range":
        min_year = validation_params.get("min_year", 1900)
        max_year = validation_params.get("max_year", 2024)
        
        # Buscar años en el texto
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        for year_str in years:
            year = int(year_str)
            if min_year <= year <= max_year:
                return True
        return False
    
    elif validation_type == "keyword_match":
        keywords = validation_params.get("keywords", [])
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    elif validation_type == "format_check":
        # Buscar patrón: título, país, año
        return bool(re.search(r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*\d{4}', text))
    
    return True

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
        
        # Obtener chat_id configurado
        from db import get_bot_config
        chat_id = get_bot_config("main_chat_id")
        
        # Seleccionar reto aleatorio
        new_challenge = random.choice(WEEKLY_CHALLENGES)
        
        # Guardar en BD
        set_challenge(new_challenge)
        
        # Notificar al grupo si tenemos chat_id
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
        
        # Obtener parámetros de validación
        validation_type = current_challenge.get('validation_type', 'always_true')
        validation_params = current_challenge.get('validation_params', {})
        
        # Verificar validación específica del reto
        if validate_challenge_text(text, validation_type, validation_params):
            bonus_points = current_challenge.get('bonus_points', 0)
            
            # Registrar completion del reto
            from db import mark_challenge_completed
            mark_challenge_completed(update.effective_user.id, current_challenge['title'])
            
            # Notificar al usuario
            await update.message.reply_text(
                f"🎯 **¡RETO COMPLETADO!**\n"
                f"'{current_challenge['title']}'\n"
                f"Bonus: +{bonus_points} puntos 🎉"
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
