from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters
)
from handlers.hashtags import handle_hashtags
from handlers.ranking import ranking_job, cmd_ranking
from handlers.retos import reto_job, cmd_reto
from handlers.spam import spam_handler
from handlers.phrases import phrase_middleware
from handlers.help import cmd_help
from handlers.start import cmd_start
from utils import cmd_mipuntaje
import asyncio
import os

async def post_init(application):
    application.job_queue.run_repeating(ranking_job, interval=604800, first=0)
    application.job_queue.run_repeating(reto_job, interval=604800, first=0)

async def fallback_debug(update, context):
    if update.message:
        print(f"[DEBUG] Mensaje recibido: {update.message.text}")
        await update.message.reply_text("📩 Recibido")

async def main():
    app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).post_init(post_init).build()

    app.add_handler(CommandHandler("ranking", cmd_ranking))
    app.add_handler(CommandHandler("reto", cmd_reto))
    app.add_handler(CommandHandler("mipuntaje", cmd_mipuntaje))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_start))

    app.add_handler(MessageHandler(filters.ALL, phrase_middleware), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hashtags))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, spam_handler), group=1)

    # fallback para confirmar recepción
    app.add_handler(MessageHandler(filters.ALL, fallback_debug), group=2)

    await app.initialize()
    await app.start()

    webhook_url = os.environ["RENDER_EXTERNAL_URL"]
    result = await app.bot.set_webhook(url=webhook_url)
    print(f"[DEBUG] Webhook set to: {webhook_url} => {result}")

    await asyncio.Event().wait()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
