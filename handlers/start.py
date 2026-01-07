import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.user_service import add_user
from services.payme_service import has_successful_payment, get_user_orders
from services.course_service import get_active_course, format_price
from keyboards.inline import get_payment_keyboard, get_back_to_payment_keyboard

logger = logging.getLogger(__name__)

# Default matn (agar kursda welcome_text bo'lmasa)
DEFAULT_WELCOME_TEXT = """
🎉 <b>Xush kelibsiz!</b>

Siz maxsus masterklassga ro'yxatdan o'tyapsiz.

👇 <b>To'lov qilish uchun pastdagi tugmani bosing.</b>
"""

NO_COURSE_TEXT = """
⚠️ <b>Hozirda aktiv kurs mavjud emas.</b>

Iltimos, keyinroq qayta urinib ko'ring.
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

    # Aktiv kursni olish
    course = await get_active_course()

    if not course:
        await update.message.reply_text(
            text=NO_COURSE_TEXT,
            parse_mode='HTML'
        )
        return

    # Kurs ma'lumotlarini context ga saqlash
    context.user_data['course_id'] = course['id']
    context.user_data['course_price'] = course['price']
    context.user_data['course_channel_id'] = course['channel_id']

    # Agar to'lov tasdiqlangan bo'lsa (shu kurs uchun)
    if await has_successful_payment(user.id, course['id']):
        await update.message.reply_text(
            text=f"✅ Siz <b>{course['name']}</b> kursiga allaqachon to'lov qilgansiz!\n\n"
                 f"🔗 Yopiq kanal: {course['channel_url']}",
            parse_mode='HTML'
        )
        return

    # State ni tozalash
    context.user_data.clear()
    context.user_data['course_id'] = course['id']

    # Welcome matn
    welcome_text = course['welcome_text'] or DEFAULT_WELCOME_TEXT

    # Narxni qo'shish
    price_text = await format_price(course['price'])
    welcome_text += f"\n\n💰 <b>Narx:</b> {price_text} so'm"

    # Welcome xabar
    await update.message.reply_text(
        text=welcome_text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(user.id, course['id'], course['price'])
    )


async def back_to_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Aktiv kursni olish
    course = await get_active_course()

    if not course:
        await query.message.edit_text(
            text=NO_COURSE_TEXT,
            parse_mode='HTML'
        )
        return

    context.user_data.clear()
    context.user_data['course_id'] = course['id']

    # Welcome matn
    welcome_text = course['welcome_text'] or DEFAULT_WELCOME_TEXT

    # Narxni qo'shish
    price_text = await format_price(course['price'])
    welcome_text += f"\n\n💰 <b>Narx:</b> {price_text} so'm"

    await query.message.edit_text(
        text=welcome_text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(query.from_user.id, course['id'], course['price'])
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
                0: '🕐',
                1: '⏳',
                2: '✅',
                -1: '❌',
                -2: '⚠️'
            }.get(order['state'], '❓')

            state_text = {
                0: 'Yaratildi',
                1: 'Kutilmoqda',
                2: 'Muvaffaqiyatli',
                -1: 'Bekor qilindi',
                -2: 'Xatolik'
            }.get(order['state'], "Noma'lum")

            amount_som = order['amount'] // 100
            history += f"{i}. {state_emoji} {amount_som:,} so'm - {state_text}\n   📅 {order['created_at']}\n\n".replace(
                ",", " ")

    # Aktiv kursni olish
    course = await get_active_course()
    course_id = course['id'] if course else None

    await query.message.edit_text(
        text=PAYMENT_HISTORY_TEXT.format(history=history),
        parse_mode='HTML',
        reply_markup=get_back_to_payment_keyboard(user_id, course_id)
    )