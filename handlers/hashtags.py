from telegram import Update
from db import add_points, get_current_challenge
from retos import get_weekly_challenge, validate_challenge_submission
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
    text_without_hashtags = re.sub(r'#\w+', '', text)
    return len(text_without_hashtags.split())

def is_spam(user_id, hashtag):
    """Detecta si un usuario está spammeando el mismo hashtag"""
    import time
    current_time = time.time()
    
    if user_id not in user_hashtag_cache:
        user_hashtag_cache[user_id] = {}
    
    user_data = user_hashtag_cache[user_id]
    
    if hashtag in user_data:
        if current_time - user_data.get("last_time", 0) < 300:
            user_data[hashtag] = user_data.get(hashtag, 0) + 1
            if user_data[hashtag] > 3:
                return True
        else:
            user_data[hashtag] = 1
    else:
        user_data[hashtag] = 1
    
    user_data["last_time"] = current_time
    return False

async def handle_hashtags(update: Update, context):
    text = update.message.text if u
