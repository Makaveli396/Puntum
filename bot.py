from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters
)
from handlers.hashtags import handle_hashtags
from handlers.ranking import ranking_job, cmd_ranking
from handlers.retos import reto_job, cmd_reto
from handlers.spam import spam_handler
from handlers.phrases import phrase_middleware
from utils import cmd_mipuntaje
from handlers.help import cmd_help
import asyncio
import os

async def post_init(application):
    application.job_queue.run_repeating(ranking_job, interval=604800, first=0)
    application.job_queue.run_repeating(reto_job, interval=604800, first=0)

async def main():
    app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).post_init(post_init).build()

    app.add_handler(MessageHandler(filters.ALL, phrase_middleware), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hashtags))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, spam_handler), group=1)
    app.add_handler(CommandHandler("ranking", cmd_ranking))
    app.add_handler(CommandHandler("reto", cmd_reto))
    app.add_handler(CommandHandler("mipuntaje", cmd_mipuntaje))
    app.add_handler(CommandHandler("help", cmd_help))

    await app.initialize()
    await app.start()

    # Webhook explícito + log
    webhook_url = os.environ["RENDER_EXTERNAL_URL"]
    await app.bot.set_webhook(url=webhook_url)
    print(f"[DEBUG] Webhook set to: {webhook_url}")

    await asyncio.Event().wait()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
