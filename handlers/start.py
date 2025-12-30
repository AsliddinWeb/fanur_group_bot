from telegram import Update
from telegram.ext import ContextTypes
from services.user_service import add_user
from services.payme_service import has_successful_payment, get_user_orders
from keyboards.inline import get_payment_keyboard, get_back_to_payment_keyboard
from config import PRIVATE_CHANNEL_URL


WELCOME_TEXT = """
🎉 <b>Tabriklaymiz!</b>

Siz <b>"2026-yilga Qadam"</b> masterklassiga ro'yxatdan o'tdingiz.

So'nggi 4 yildan beri xotira kuchaytirish va shaxsiy rivojlanish bilan shug'ullanaman.

🧠 Eslab qolish bo'yicha jahon reytingida <b>TOP–22</b> natijaga erishganman.
📘 <b>"Super 30 kun"</b> kundaligi va cheklistlar muallifiman.
👥 Minglab insonlarga kuchli xotira va aniq maqsad qo'yishda yordam berganman.

🚀 <b>"2026-yilga Qadam"</b> —
📆 1 haftalik intensiv masterklass
🎯 2026-yil uchun aniq maqsadlar
🧠 Tez va oson natija beradigan usullar

❗ Masterklass minimal summada, lekin qiymati juda yuqori.

🔥 Siz bu yerga 2026-yilda maqsadlaringizga erishish uchun keldingiz.
Oxirigacha harakat qiling va bizning safimizga qo'shiling!

👇 <b>To'lov qilish uchun pastdagi tugmani bosing.</b>
"""

PAYMENT_HISTORY_TEXT = """
📋 <b>Sizning to'lovlaringiz:</b>

{history}
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Userni bazaga saqlash
    await add_user(
        chat_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )

    # Agar to'lov tasdiqlangan bo'lsa
    if await has_successful_payment(user.id):
        await update.message.reply_text(
            text=f"✅ Siz allaqachon to'lov qilgansiz!\n\n🔗 Yopiq kanal: {PRIVATE_CHANNEL_URL}",
            parse_mode='HTML'
        )
        return

    # State ni tozalash
    context.user_data.clear()

    # Welcome xabar
    await update.message.reply_text(
        text=WELCOME_TEXT,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(user.id)
    )


async def back_to_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.message.edit_text(
        text=WELCOME_TEXT,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(query.from_user.id)
    )


async def payment_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    orders = await get_user_orders(user_id)

    if not orders:
        history = "❌ Sizda hali to'lovlar yo'q."
    else:
        history = ""
        for i, order in enumerate(orders, 1):
            state_emoji = {
                0: '🕐',   # yaratildi
                1: '⏳',   # pending
                2: '✅',   # success
                -1: '❌',  # cancelled
                -2: '⚠️'   # failed
            }.get(order['state'], '❓')

            state_text = {
                0: 'Yaratildi',
                1: 'Kutilmoqda',
                2: 'Muvaffaqiyatli',
                -1: 'Bekor qilindi',
                -2: 'Xatolik'
            }.get(order['state'], "Noma'lum")

            amount_som = order['amount'] // 100  # tiyin -> so'm
            history += f"{i}. {state_emoji} {amount_som:,} so'm - {state_text}\n   📅 {order['created_at']}\n\n".replace(",", " ")

    await query.message.edit_text(
        text=PAYMENT_HISTORY_TEXT.format(history=history),
        parse_mode='HTML',
        reply_markup=get_back_to_payment_keyboard(user_id)
    )