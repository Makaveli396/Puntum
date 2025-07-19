from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters
)
from handlers.hashtags import handle_hashtags
from handlers.ranking import ranking_job, cmd_ranking
from handlers.retos import reto_job, cmd_reto, cmd_nuevo_reto
from handlers.spam import spam_handler
from handlers.phrases import phrase_middleware
from handlers.help import cmd_help
from handlers.start import cmd_start
from utils import cmd_mipuntaje
from db import set_chat_config, get_chat_config
import asyncio
import os
from aiohttp import web
from aiohttp.web import Request, Response
import json
from db import create_tables
create_tables()

# CONFIGURACIÓN CRÍTICA: Chat principal para jobs automáticos
MAIN_CHAT_ID = os.environ.get("MAIN_CHAT_ID")  # Configurar en variables de entorno
if not MAIN_CHAT_ID:
    print("[WARNING] MAIN_CHAT_ID no configurado - jobs automáticos deshabilitados")

async def post_init(application):
    """Inicializa los jobs automáticos con chat_id configurado"""
    if MAIN_CHAT_ID:
        # Job ranking semanal: domingos a las 20:00 UTC
        application.job_queue.run_repeating(
            ranking_job, 
            interval=604800,  # 7 días en segundos
            first=0,
            data=int(MAIN_CHAT_ID)  # Pasar chat_id como data
        )
        
        # Job reto semanal: lunes a las 10:00 UTC
        application.job_queue.run_repeating(
            reto_job, 
            interval=604800,  # 7 días en segundos
            first=3600,  # 1 hora después del ranking
            data=int(MAIN_CHAT_ID)  # Pasar chat_id como data
        )
        
        # Configurar el chat en la base de datos
        try:
            set_chat_config(int(MAIN_CHAT_ID), "Chat Principal Bot", True, True)
            print(f"[INFO] Jobs configurados para chat_id: {MAIN_CHAT_ID}")
        except Exception as e:
            print(f"[ERROR] Error configurando chat en DB: {e}")
    else:
        print("[WARNING] Jobs automáticos no configurados - falta MAIN_CHAT_ID")

async def fallback_debug(update, context):
    if update.message:
        print(f"[DEBUG] Mensaje recibido: {update.message.text}")

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
        print(f"[ERROR] Error procesando webhook: {e}")
        return Response(text="Error", status=500)

async def health_check(request: Request) -> Response:
    """Health check para Render"""
    return Response(text="Bot is running!")

async def cmd_configurar_chat(update, context):
    """Comando para administradores: configurar chat actual para jobs automáticos"""
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    
    if not ADMIN_IDS or update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Solo administradores pueden usar este comando")
        return
    
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Chat Privado"
    
    try:
        set_chat_config(chat_id, chat_title, True, True)
        await update.message.reply_text(
            f"✅ Chat configurado correctamente\n"
            f"📱 ID: `{chat_id}`\n"
            f"📝 Título: {chat_title}\n"
            f"🔄 Recibirá rankings y retos automáticos"
        )
        print(f"[INFO] Chat {chat_id} configurado manualmente")
    except Exception as e:
        print(f"[ERROR] Error configurando chat: {e}")
        await update.message.reply_text("❌ Error al configurar el chat")

async def cmd_test_job(update, context):
    """Comando de prueba para administradores"""
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    
    if not ADMIN_IDS or update.effective_user.id not in ADMIN_IDS:
        return
    
    if len(context.args) > 0 and context.args[0] == "ranking":
        # Test del job de ranking
        await ranking_job(context)
        await update.message.reply_text("✅ Job de ranking ejecutado manualmente")
    elif len(context.args) > 0 and context.args[0] == "reto":
        # Test del job de reto
        await reto_job(context)
        await update.message.reply_text("✅ Job de reto ejecutado manualmente")
    else:
        await update.message.reply_text(
            "🧪 Comandos de prueba:\n"
            "`/testjob ranking` - Ejecutar ranking manual\n"
            "`/testjob reto` - Ejecutar reto manual"
        )

async def setup_bot():
    """Configura el bot de Telegram"""
    global bot_app
    
    bot_app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).post_init(post_init).build()
    
    # COMANDOS (siempre primero)
    bot_app.add_handler(CommandHandler("start", cmd_start))
    bot_app.add_handler(CommandHandler("help", cmd_help))
    bot_app.add_handler(CommandHandler("ranking", cmd_ranking))
    bot_app.add_handler(CommandHandler("reto", cmd_reto))
    bot_app.add_handler(CommandHandler("mipuntaje", cmd_mipuntaje))
    
    # COMANDOS ADMIN
    bot_app.add_handler(CommandHandler("configurarchat", cmd_configurar_chat))
    bot_app.add_handler(CommandHandler("nuevoreto", cmd_nuevo_reto))
    bot_app.add_handler(CommandHandler("testjob", cmd_test_job))
    
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
    print(f"[INFO] Webhook configurado: {webhook_url} => {result}")
    
    return bot_app

async def main():
    """Función principal"""
    # Mostrar configuración al inicio
    print("[INFO] ==> Configuración del Bot <==")
    print(f"[INFO] MAIN_CHAT_ID: {MAIN_CHAT_ID}")
    print(f"[INFO] ADMIN_IDS: {os.environ.get('ADMIN_IDS', 'No configurado')}")
    print(f"[INFO] BOT_TOKEN: {'✅ Configurado' if os.environ.get('BOT_TOKEN') else '❌ Falta'}")
    print(f"[INFO] RENDER_EXTERNAL_URL: {os.environ.get('RENDER_EXTERNAL_URL', 'No configurado')}")
    
    # Configurar el bot
    await setup_bot()
    
    # Crear servidor web con aiohttp
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/', health_check)
    
    # Obtener puerto de Render
    port = int(os.environ.get("PORT", 8000))
    
    print(f"[INFO] Iniciando servidor en puerto {port}")
    
    # Iniciar servidor
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print("[INFO] Bot y servidor iniciados correctamente")
    print("[INFO] Para configurar un chat: /configurarchat")
    print("[INFO] Para probar jobs: /testjob ranking o /testjob reto")
    
    # Mantener corriendo
    await asyncio.Event().wait()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
