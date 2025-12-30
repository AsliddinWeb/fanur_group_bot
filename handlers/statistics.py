from telegram import Update
from telegram.ext import ContextTypes
from middlewares.admin_check import admin_required_callback
from keyboards.inline import get_back_keyboard
from services.stats_service import get_all_stats
from utils.helpers import format_stats


@admin_required_callback
async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    stats = await get_all_stats()
    stats_text = format_stats(stats)

    await query.message.edit_text(
        text=stats_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )