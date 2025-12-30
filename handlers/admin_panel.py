from telegram import Update
from telegram.ext import ContextTypes
from middlewares.admin_check import admin_required, admin_required_callback
from keyboards.inline import get_admin_panel_keyboard

ADMIN_PANEL_TEXT = """
🔐 <b>Admin Panel</b>

Quyidagi bo'limlardan birini tanlang:
"""


@admin_required
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=ADMIN_PANEL_TEXT,
        parse_mode='HTML',
        reply_markup=get_admin_panel_keyboard()
    )


@admin_required_callback
async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # State ni tozalash
    context.user_data.clear()

    # Agar xabar rasm bo'lsa, o'chirib yangisini yuboramiz
    try:
        await query.message.edit_text(
            text=ADMIN_PANEL_TEXT,
            parse_mode='HTML',
            reply_markup=get_admin_panel_keyboard()
        )
    except:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=ADMIN_PANEL_TEXT,
            parse_mode='HTML',
            reply_markup=get_admin_panel_keyboard()
        )


@admin_required_callback
async def cancel_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("❌ Bekor qilindi!")

    # State ni tozalash
    context.user_data.clear()

    try:
        await query.message.edit_text(
            text=ADMIN_PANEL_TEXT,
            parse_mode='HTML',
            reply_markup=get_admin_panel_keyboard()
        )
    except:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=ADMIN_PANEL_TEXT,
            parse_mode='HTML',
            reply_markup=get_admin_panel_keyboard()
        )