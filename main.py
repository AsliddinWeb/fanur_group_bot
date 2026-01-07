import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN, BOT_NAME, LOG_LEVEL
from database.models import create_tables, migrate_add_course_id

# Logging sozlash
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Handlers
from handlers.start import (
    start_command,
    back_to_payment_callback,
    payment_history_callback
)
from handlers.admin_panel import admin_command, admin_back_callback, cancel_action_callback
from handlers.statistics import stats_callback
from handlers.broadcast import broadcast_callback, receive_broadcast_content
from handlers.user_search import search_callback, receive_search_query
from handlers.export import export_callback, export_csv_callback, export_excel_callback
from handlers.admin_manage import (
    admin_manage_callback,
    add_admin_callback,
    remove_admin_callback,
    list_admins_callback,
    receive_add_admin,
    receive_remove_admin
)
from handlers.subscription import (
    subscription_settings_callback,
    toggle_subscription_callback,
    change_channel_callback,
    receive_channel_id
)
from handlers.payment import (
    admin_payme_callback,
    payme_stats_callback,
    payme_recent_callback
)
from handlers.course_admin import (
    courses_menu_callback,
    add_course_callback,
    course_detail_callback,
    activate_course_callback,
    delete_course_callback,
    edit_course_menu_callback,
    edit_course_name_callback,
    edit_course_price_callback,
    edit_course_channel_callback,
    edit_course_welcome_callback,
    receive_course_name,
    receive_course_price,
    receive_course_channel_id,
    receive_course_channel_url,
    receive_course_welcome_text,
    receive_edit_name,
    receive_edit_price,
    receive_edit_channel_id,
    receive_edit_channel_url,
    receive_edit_welcome_text
)

# API
from api.payme import router as payme_router

# Global bot application
bot_app = None


async def handle_text_messages(update, context):
    """Text xabarlarni state bo'yicha yo'naltirish"""
    state = context.user_data.get('state')

    # Broadcast
    if state == 'waiting_broadcast':
        await receive_broadcast_content(update, context)

    # Search
    elif state == 'waiting_search':
        await receive_search_query(update, context)

    # Admin manage
    elif state == 'waiting_add_admin':
        await receive_add_admin(update, context)
    elif state == 'waiting_remove_admin':
        await receive_remove_admin(update, context)

    # Subscription
    elif state == 'waiting_channel_id':
        await receive_channel_id(update, context)

    # Course - yangi kurs qo'shish
    elif state == 'waiting_course_name':
        await receive_course_name(update, context)
    elif state == 'waiting_course_price':
        await receive_course_price(update, context)
    elif state == 'waiting_course_channel_id':
        await receive_course_channel_id(update, context)
    elif state == 'waiting_course_channel_url':
        await receive_course_channel_url(update, context)
    elif state == 'waiting_course_welcome_text':
        await receive_course_welcome_text(update, context)

    # Course - tahrirlash
    elif state == 'waiting_edit_name':
        await receive_edit_name(update, context)
    elif state == 'waiting_edit_price':
        await receive_edit_price(update, context)
    elif state == 'waiting_edit_channel_id':
        await receive_edit_channel_id(update, context)
    elif state == 'waiting_edit_channel_url':
        await receive_edit_channel_url(update, context)
    elif state == 'waiting_edit_welcome_text':
        await receive_edit_welcome_text(update, context)


def setup_bot() -> Application:
    """Bot handlerlarini sozlash"""
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))

    # Payment callbacks
    app.add_handler(CallbackQueryHandler(back_to_payment_callback, pattern="^back_to_payment$"))
    app.add_handler(CallbackQueryHandler(payment_history_callback, pattern="^payment_history$"))

    # Admin panel callbacks
    app.add_handler(CallbackQueryHandler(admin_back_callback, pattern="^admin_back$"))
    app.add_handler(CallbackQueryHandler(cancel_action_callback, pattern="^cancel_action$"))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(export_callback, pattern="^admin_export$"))
    app.add_handler(CallbackQueryHandler(export_csv_callback, pattern="^export_csv$"))
    app.add_handler(CallbackQueryHandler(export_excel_callback, pattern="^export_excel$"))
    app.add_handler(CallbackQueryHandler(admin_manage_callback, pattern="^admin_manage$"))
    app.add_handler(CallbackQueryHandler(list_admins_callback, pattern="^list_admins$"))
    app.add_handler(CallbackQueryHandler(subscription_settings_callback, pattern="^admin_subscription$"))
    app.add_handler(CallbackQueryHandler(toggle_subscription_callback, pattern="^toggle_subscription$"))

    # Admin Payme callbacks
    app.add_handler(CallbackQueryHandler(admin_payme_callback, pattern="^admin_payme$"))
    app.add_handler(CallbackQueryHandler(payme_stats_callback, pattern="^payme_stats$"))
    app.add_handler(CallbackQueryHandler(payme_recent_callback, pattern="^payme_recent$"))

    # Courses callbacks
    app.add_handler(CallbackQueryHandler(courses_menu_callback, pattern="^admin_courses$"))
    app.add_handler(CallbackQueryHandler(add_course_callback, pattern="^add_course$"))
    app.add_handler(CallbackQueryHandler(course_detail_callback, pattern="^course_detail_"))
    app.add_handler(CallbackQueryHandler(activate_course_callback, pattern="^activate_course_"))
    app.add_handler(CallbackQueryHandler(delete_course_callback, pattern="^delete_course_"))
    app.add_handler(CallbackQueryHandler(edit_course_menu_callback, pattern="^edit_course_"))
    app.add_handler(CallbackQueryHandler(edit_course_name_callback, pattern="^edit_name_"))
    app.add_handler(CallbackQueryHandler(edit_course_price_callback, pattern="^edit_price_"))
    app.add_handler(CallbackQueryHandler(edit_course_channel_callback, pattern="^edit_channel_"))
    app.add_handler(CallbackQueryHandler(edit_course_welcome_callback, pattern="^edit_welcome_"))

    # Broadcast
    app.add_handler(CallbackQueryHandler(broadcast_callback, pattern="^admin_broadcast$"))

    # Search
    app.add_handler(CallbackQueryHandler(search_callback, pattern="^admin_search$"))

    # Admin manage
    app.add_handler(CallbackQueryHandler(add_admin_callback, pattern="^add_admin$"))
    app.add_handler(CallbackQueryHandler(remove_admin_callback, pattern="^remove_admin$"))

    # Channel change
    app.add_handler(CallbackQueryHandler(change_channel_callback, pattern="^change_channel$"))

    # Message handlers
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_text_messages
    ))

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI startup va shutdown"""
    global bot_app

    # Database yaratish (migration ichida)
    await create_tables()

    logger.info("✅ Database tayyor!")

    # Bot ishga tushirish
    bot_app = setup_bot()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info(f"✅ {BOT_NAME} ishga tushdi!")

    yield

    # Shutdown
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()
    logger.info(f"🛑 {BOT_NAME} to'xtadi!")


# FastAPI app
app = FastAPI(
    title=BOT_NAME,
    description="Payme to'lov integratsiyasi bilan Telegram bot",
    version="2.0.0",
    lifespan=lifespan
)

# Payme router
app.include_router(payme_router, prefix="/api", tags=["Payme"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "bot": BOT_NAME, "message": "Bot ishlayapti!"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "bot": BOT_NAME}


def get_bot() -> Application:
    """Bot instansini olish (webhook uchun)"""
    return bot_app


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )