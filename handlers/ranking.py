from db import get_top10
from telegram import Update

def cmd_ranking(update: Update, context):
    top = get_top10()
    msg = "🎬 Top 10 Cinéfilos:\n"
    for i, (user, pts) in enumerate(top, 1):
        msg += f"{i}. {user} - {pts} pts\n"
    update.message.reply_text(msg)

def ranking_job(context): pass
