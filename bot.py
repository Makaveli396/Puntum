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
from aiohttp import web
from aiohttp.web import Request, Response
import json

async def post_init(application):
    application.job_queue.run_repeating(ranking_job, interval=604800, first=0)
    application.job_queue.run_repeating(reto_job, interval=604800, first=0)

async def fallback_debug(update, context):
    if update.message:
        print(f"[DEBUG] Mensaje recibido: {update.message.text}")
        # REMOVIDO: await update.message.reply_text("📩 Recibido")

# Variable global para el bot
bot_app = None

async def webhook_handler(request: Request) -> Response:
    """Maneja las actualizaciones de Telegram"""
    try:
        body = await request.text()
        update_dict = json.loads(body)
        
        if bot_app:
            from telegram import Update
            update = Update.de_json(update_dict, bot_app.bot)
            await bot_app.process_update(update)
        
        return Response(text="OK")
    except Exception as e:
        print(f"Error procesando webhook: {e}")
        return Response(text="Error", status=500)

async def health_check(request: Request) -> Response:
    """Health check para Render"""
    return Response(text="Bot is running!")

async def setup_bot():
    """Configura el bot de Telegram"""
    global bot_app
    
    bot_app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).post_init(post_init).build()
    
    # COMANDOS (siempre primero)
    bot_app.add_handler(CommandHandler("ranking", cmd_ranking))
    bot_app.add_handler(CommandHandler("reto", cmd_reto))
    bot_app.add_handler(CommandHandler("mipuntaje", cmd_mipuntaje))
    bot_app.add_handler(CommandHandler("help", cmd_help))
    bot_app.add_handler(CommandHandler("start", cmd_start))
    
    # HANDLERS DE MENSAJES (en orden de prioridad)
    # Group 0: Hashtags (MÁS IMPORTANTE)
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hashtags), group=0)
    
    # Group 1: Detección de spam
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, spam_handler), group=1)
    
    # Group 2: Frases trigger (solo "cine")
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, phrase_middleware), group=2)
    
    # Group 3: Fallback debug (sin respuesta automática)
    bot_app.add_handler(MessageHandler(filters.ALL, fallback_debug), group=3)
    
    # Inicializar
    await bot_app.initialize()
    await bot_app.start()
    
    # Configurar webhook
    webhook_url = f"{os.environ['RENDER_EXTERNAL_URL']}/webhook"
    result = await bot_app.bot.set_webhook(url=webhook_url)
    print(f"[DEBUG] Webhook configurado: {webhook_url} => {result}")
    
    return bot_app

async def main():
    """Función principal"""
    # Configurar el bot
    await setup_bot()
    
    # Crear servidor web con aiohttp
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/', health_check)
    
    # Obtener puerto de Render
    port = int(os.environ.get("PORT", 8000))
    
    print(f"[DEBUG] Iniciando servidor en puerto {port}")
    
    # Iniciar servidor
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print("[DEBUG] Bot y servidor iniciados correctamente")
    
    # Mantener corriendo
    await asyncio.Event().wait()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
  
