from db import add_points
from telegram import Update
import re

POINTS = {
    "#aporte": 3,
    "#recomendación": 5,
    "#reseña": 7,
    "#crítica": 10,
    "#debate": 4,
    "#pregunta": 2,
    "#spoiler": 1,
}

# Cache para antispam - almacena {user_id: {"hashtag": count, "last_message_time": timestamp}}
user_hashtag_cache = {}

def count_words(text):
    """Cuenta palabras en un texto, excluyendo hashtags"""
    # Remover hashtags y contar palabras
    text_without_hashtags = re.sub(r'#\w+', '', text)
    words = len(text_without_hashtags.split())
    return words

def is_spam(user_id, hashtag):
    """Detecta si un usuario está spammeando el mismo hashtag"""
    import time
    current_time = time.time()
    
    if user_id not in user_hashtag_cache:
        user_hashtag_cache[user_id] = {}
    
    user_data = user_hashtag_cache[user_id]
    
    # Si es el mismo hashtag en menos de 5 minutos
    if hashtag in user_data:
        if current_time - user_data.get("last_time", 0) < 300:  # 5 minutos
            user_data[hashtag] = user_data.get(hashtag, 0) + 1
            if user_data[hashtag] > 3:  # Máximo 3 veces el mismo hashtag en 5 min
                return True
        else:
            user_data[hashtag] = 1
    else:
        user_data[hashtag] = 1
    
    user_data["last_time"] = current_time
    return False

async def handle_hashtags(update: Update, context):
    text = update.message.text if update.message and update.message.text else ""
    user = update.effective_user
    points = 0
    found_tags = []
    warnings = []
    
    print(f"[DEBUG] handle_hashtags: {text}")
    
    for tag, value in POINTS.items():
        if tag in text.lower():
            # Verificar spam
            if is_spam(user.id, tag):
                warnings.append(f"⚠️ {tag}: Detectado spam. Usa hashtags con moderación.")
                continue
            
            # Validaciones específicas
            if tag == "#reseña":
                word_count = count_words(text)
                if word_count < 50:
                    warnings.append(f"❌ {tag}: Necesitas mínimo 50 palabras. Tienes {word_count}.")
                    continue
            
            elif tag == "#crítica":
                word_count = count_words(text)
                if word_count < 100:
                    warnings.append(f"❌ {tag}: Necesitas mínimo 100 palabras. Tienes {word_count}.")
                    continue
            
            elif tag == "#recomendación":
                # Buscar patrón: título, país, año
                has_pattern = bool(re.search(r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*\d{4}', text))
                if not has_pattern:
                    warnings.append(f"💡 {tag}: Incluye formato 'Título, País, Año' para más puntos.")
                    # No bloqueamos, pero damos menos puntos
                    value = 3  # Reducimos de 5 a 3
            
            points += value
            found_tags.append(f"{tag} (+{value})")
    
    # Respuesta al usuario
    if points > 0 or warnings:
        add_points(user.id, user.username, points)
        print(f"[DEBUG] {points} puntos otorgados a {user.username}")
        
        response = ""
        if points > 0:
            tags_text = ", ".join(found_tags)
            response += f"✅ +{points} puntos por: {tags_text}\n"
        
        if warnings:
            response += "\n".join(warnings)
        
        await update.message.reply_text(response.strip())
    
    # Detectar spam general (palabras como "gratis", "oferta", etc.)
    spam_words = ["gratis", "oferta", "descuento", "promoción", "gana dinero", "click aquí"]
    if any(spam_word in text.lower() for spam_word in spam_words):
        await update.message.reply_text("🛑 ¡Cuidado con el spam! Esto es un grupo de cine, no de ofertas.")
