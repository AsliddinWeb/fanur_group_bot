from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from middlewares.admin_check import admin_required_callback
from keyboards.inline import get_subscription_settings_keyboard, get_back_keyboard, get_cancel_keyboard
from services.settings_service import (
    is_force_subscribe_enabled,
    enable_force_subscribe,
    disable_force_subscribe,
    get_channel_id,
    set_channel_id
)
from config import CHANNEL_ID

# States
WAITING_CHANNEL_ID = 1


@admin_required_callback
async def subscription_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    is_enabled = await is_force_subscribe_enabled()
    channel = await get_channel_id() or CHANNEL_ID or "Belgilanmagan"

    status = "✅ Yoqilgan" if is_enabled else "❌ O'chirilgan"

    await query.message.edit_text(
        text=f"⚙️ <b>Majburiy obuna sozlamalari</b>\n\n"
             f"📊 Holati: {status}\n"
             f"📢 Kanal: <code>{channel}</code>",
        parse_mode='HTML',
        reply_markup=get_subscription_settings_keyboard(is_enabled)
    )


@admin_required_callback
async def toggle_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    is_enabled = await is_force_subscribe_enabled()

    if is_enabled:
        await disable_force_subscribe()
        await query.answer("❌ Majburiy obuna o'chirildi!", show_alert=True)
    else:
        await enable_force_subscribe()
        await query.answer("✅ Majburiy obuna yoqildi!", show_alert=True)

    # Sahifani yangilash
    new_status = not is_enabled
    channel = await get_channel_id() or CHANNEL_ID or "Belgilanmagan"
    status = "✅ Yoqilgan" if new_status else "❌ O'chirilgan"

    await query.message.edit_text(
        text=f"⚙️ <b>Majburiy obuna sozlamalari</b>\n\n"
             f"📊 Holati: {status}\n"
             f"📢 Kanal: <code>{channel}</code>",
        parse_mode='HTML',
        reply_markup=get_subscription_settings_keyboard(new_status)
    )


@admin_required_callback
async def change_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['state'] = 'waiting_channel_id'

    await query.message.edit_text(
        text="📝 <b>Kanal o'zgartirish</b>\n\n"
             "Yangi kanal ID yoki username yuboring.\n\n"
             "Misol: <code>@channel_username</code> yoki <code>-1001234567890</code>\n\n"
             "⚠️ Bot kanalda admin bo'lishi kerak!",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_CHANNEL_ID


async def receive_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'waiting_channel_id':
        return

    new_channel = update.message.text.strip()

    # Tekshirish
    try:
        chat = await context.bot.get_chat(new_channel)
        await set_channel_id(new_channel)

        await update.message.reply_text(
            text=f"✅ Kanal muvaffaqiyatli o'zgartirildi!\n\n"
                 f"📢 Yangi kanal: <code>{new_channel}</code>\n"
                 f"📛 Nomi: {chat.title}",
            parse_mode='HTML',
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(
            text=f"❌ Xatolik! Kanal topilmadi yoki bot admin emas.\n\n"
                 f"Xato: {str(e)}",
            reply_markup=get_back_keyboard()
        )

    context.user_data.clear()
    return ConversationHandler.END