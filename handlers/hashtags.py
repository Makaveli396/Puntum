from db import add_points
from telegram import Update

POINTS = {
    "#aporte": 3,
    "#recomendación": 5,
    "#reseña": 7,
    "#crítica": 10,
    "#debate": 4,
    "#pregunta": 2,
    "#spoiler": 1,
}

async def handle_hashtags(update: Update, context):
    text = update.message.text.lower()
    user = update.effective_user
    points = 0

    for tag, value in POINTS.items():
        if tag in text:
            points += value

    add_points(user.id, user.username, points)
