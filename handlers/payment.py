from telegram import Update
from telegram.ext import ContextTypes
from middlewares.admin_check import admin_required_callback
from keyboards.inline import get_payme_stats_keyboard, get_back_keyboard
from services.payme_service import get_payme_stats, get_user_orders
from services.user_service import get_user


@admin_required_callback
async def admin_payme_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        text="💰 <b>Payme to'lovlar boshqaruvi</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        parse_mode='HTML',
        reply_markup=get_payme_stats_keyboard()
    )


@admin_required_callback
async def payme_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    stats = await get_payme_stats()

    # Tiyin -> So'm
    total_amount_som = stats['total_amount'] // 100

    text = f"""
📊 <b>Payme statistikasi</b>

📋 Jami to'lovlar: <b>{stats['total']}</b> ta
✅ Muvaffaqiyatli: <b>{stats['success']}</b> ta
⏳ Kutilmoqda: <b>{stats['pending']}</b> ta
❌ Bekor qilingan: <b>{stats['cancelled']}</b> ta

💰 Jami tushum: <b>{total_amount_som:,}</b> so'm
""".replace(",", " ")

    await query.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )


@admin_required_callback
async def payme_recent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    from services.payme_service import get_recent_orders
    orders = await get_recent_orders(10)

    if not orders:
        await query.message.edit_text(
            text="📋 Hali to'lovlar yo'q.",
            parse_mode='HTML',
            reply_markup=get_back_keyboard()
        )
        return

    text = "📋 <b>Oxirgi 10 ta to'lov:</b>\n\n"

    for order in orders:
        state_emoji = {
            0: '🕐',
            1: '⏳',
            2: '✅',
            -1: '❌',
            -2: '⚠️'
        }.get(order['state'], '❓')

        amount_som = order['amount'] // 100

        text += (
            f"{state_emoji} <code>{order['user_id']}</code> | "
            f"{amount_som:,} so'm | "
            f"{order['created_at']}\n"
        ).replace(",", " ")

    await query.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )