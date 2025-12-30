from telegram import Update, Bot
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from services.settings_service import is_force_subscribe_enabled, get_channel_id
from keyboards.inline import get_check_subscription_keyboard
from config import CHANNEL_ID


async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        channel = await get_channel_id() or CHANNEL_ID
        if not channel:
            return True

        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError:
        return True


async def subscription_required(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not await is_force_subscribe_enabled():
        return True

    user_id = update.effective_user.id
    is_subscribed = await check_subscription(context.bot, user_id)

    if not is_subscribed:
        text = "❗️ Botdan foydalanish uchun kanalimizga obuna bo'ling!"

        # Message yoki callback query ekanligini tekshirish
        if update.message:
            await update.message.reply_text(
                text=text,
                reply_markup=get_check_subscription_keyboard()
            )
        elif update.callback_query:
            await update.callback_query.message.edit_text(
                text=text,
                reply_markup=get_check_subscription_keyboard()
            )
        return False

    return True