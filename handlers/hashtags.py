from telegram import Update
from db import add_points
from handlers.retos import get_weekly_challenge, validate_challenge_submission, get_current_challenge
from handlers.retos_diarios import get_today_challenge
from handlers.phrases import get_random_reaction
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

user_hashtag_cache = {}

def count_words(text):
    text_without_hashtags = re.sub(r'#\w+', '', text)
    return len(text_without_hashtags.split())

def is_spam(user_id, hashtag):
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
    text = update.message.text if update.message and update.message.text else ""
    user = update.effective_user
    points = 0
    found_tags = []
    warnings = []
    response = ""

    print(f"[DEBUG] handle_hashtags: {text}")

    for tag, value in POINTS.items():
        if tag in text.lower():
            if is_spam(user.id, tag):
                warnings.append(f"⚠️ {tag}: Detectado spam. Usa hashtags con moderación.")
                continue

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
                has_pattern = bool(re.search(r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*\d{4}', text))
                if not has_pattern:
                    warnings.append(f"💡 {tag}: Incluye formato 'Título, País, Año' para más puntos.")
                    value = 3

            points += value
            found_tags.append(f"{tag} (+{value})")

    if points > 0 or warnings:
        result = add_points(
            user.id,
            user.username,
            points,
            hashtag=None,
            message_text=text,
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            is_challenge_bonus=False,
            context=context
        )

        if points > 0:
            tags_text = ", ".join(found_tags)
            tag_main = found_tags[0].split()[0] if found_tags else "default"
            reaction = get_random_reaction(tag_main, user.id)
            response += f"✅ +{points} puntos por: {tags_text}\n{reaction}\n"

        if warnings:
            response += "\n".join(warnings)

        # Reto semanal
        try:
            challenge_text = get_current_challenge()
            current_challenge = get_weekly_challenge()
            if not challenge_text:
                if current_challenge["hashtag"] in text.lower():
                    if validate_challenge_submission(current_challenge, text):
                        bonus = current_challenge["bonus_points"]
                        bonus_result = add_points(
                            user.id,
                            user.username,
                            bonus,
                            hashtag=current_challenge["hashtag"],
                            message_text=text,
                            chat_id=update.effective_chat.id,
                            message_id=update.message.message_id,
                            is_challenge_bonus=True,
                            context=context
                        )
                        response += f"\n🎯 ¡Cumpliste el reto semanal! Bonus: +{bonus} puntos 🎉"
        except Exception as e:
            print(f"[ERROR] Validando reto semanal: {e}")

        # Reto diario
        try:
            daily = get_today_challenge()
            cumple = False

            if "hashtag" in daily and daily["hashtag"] in text.lower():
                cumple = True
            elif "keywords" in daily:
                cumple = any(word in text.lower() for word in daily["keywords"])

            if cumple and "min_words" in daily:
                word_count = count_words(text)
                if word_count < daily["min_words"]:
                    cumple = False

            if cumple:
                daily_bonus = daily["bonus_points"]
                bonus_result = add_points(
                    user.id,
                    user.username,
                    daily_bonus,
                    hashtag="(reto_diario)",
                    message_text=text,
                    chat_id=update.effective_chat.id,
                    message_id=update.message.message_id,
                    is_challenge_bonus=True,
                    context=context
                )
                response += f"\n🎯 ¡Cumpliste el reto diario! Bonus: +{daily_bonus} puntos 🎉"
        except Exception as e:
            print(f"[ERROR] Validando reto diario: {e}")

        await update.message.reply_text(response.strip())

    # Antispam general
    spam_words = ["gratis", "oferta", "descuento", "promoción", "gana dinero", "click aquí"]
    if any(spam_word in text.lower() for spam_word in spam_words):
        await update.message.reply_text("🛑 ¡Cuidado con el spam! Esto es un grupo de cine, no de ofertas.")
