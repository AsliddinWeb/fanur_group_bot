from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from services.admin_service import is_admin


def admin_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        if not await is_admin(user_id):
            await update.message.reply_text("⛔️ Sizda bu buyruqdan foydalanish huquqi yo'q!")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def admin_required_callback(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        if not await is_admin(user_id):
            await update.callback_query.answer("⛔️ Sizda ruxsat yo'q!", show_alert=True)
            return

        return await func(update, context, *args, **kwargs)

    return wrapper