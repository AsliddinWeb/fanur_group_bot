from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from middlewares.admin_check import admin_required_callback
from keyboards.inline import get_back_keyboard, get_cancel_keyboard
from services.user_service import search_user_by_id, search_user_by_username
from utils.helpers import format_user_info

# States
WAITING_SEARCH_QUERY = 1


@admin_required_callback
async def search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['state'] = 'waiting_search'

    await query.message.edit_text(
        text="🔍 <b>Foydalanuvchi qidirish</b>\n\n"
             "Foydalanuvchining ID yoki username'ini yuboring.\n\n"
             "Misol: <code>123456789</code> yoki <code>@username</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_SEARCH_QUERY


async def receive_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'waiting_search':
        return

    query_text = update.message.text.strip()

    users = []

    # ID bo'yicha qidirish
    if query_text.isdigit():
        user = await search_user_by_id(int(query_text))
        if user:
            users = [user]
    # Username bo'yicha qidirish
    else:
        username = query_text.replace('@', '')
        users = await search_user_by_username(username)

    if not users:
        await update.message.reply_text(
            text="❌ Foydalanuvchi topilmadi!",
            reply_markup=get_back_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END

    if len(users) == 1:
        user_info = format_user_info(users[0])
        await update.message.reply_text(
            text=user_info,
            parse_mode='HTML',
            reply_markup=get_back_keyboard()
        )
    else:
        result_text = f"🔍 <b>Topildi: {len(users)} ta</b>\n\n"
        for user in users[:10]:  # Max 10 ta ko'rsatish
            result_text += (
                f"👤 {user['first_name'] or '-'} | "
                f"<code>{user['chat_id']}</code> | "
                f"@{user['username'] or '-'}\n"
            )

        if len(users) > 10:
            result_text += f"\n... va yana {len(users) - 10} ta"

        await update.message.reply_text(
            text=result_text,
            parse_mode='HTML',
            reply_markup=get_back_keyboard()
        )

    context.user_data.clear()
    return ConversationHandler.END