import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from middlewares.admin_check import admin_required_callback
from keyboards.inline import (
    get_courses_keyboard,
    get_course_detail_keyboard,
    get_course_edit_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
    get_admin_panel_keyboard
)
from services.course_service import (
    create_course,
    get_course,
    get_all_courses,
    get_active_course,
    update_course,
    set_active_course,
    delete_course,
    format_price
)

logger = logging.getLogger(__name__)

# States
WAITING_COURSE_NAME = 1
WAITING_COURSE_PRICE = 2
WAITING_COURSE_CHANNEL_ID = 3
WAITING_COURSE_CHANNEL_URL = 4
WAITING_COURSE_WELCOME_TEXT = 5
WAITING_COURSE_DESCRIPTION = 6
WAITING_EDIT_NAME = 7
WAITING_EDIT_PRICE = 8
WAITING_EDIT_CHANNEL_ID = 9
WAITING_EDIT_CHANNEL_URL = 10
WAITING_EDIT_WELCOME_TEXT = 11


@admin_required_callback
async def courses_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kurslar menyusi"""
    query = update.callback_query
    await query.answer()

    courses = await get_all_courses()
    active_course = await get_active_course()

    text = "📚 <b>Kurslar boshqaruvi</b>\n\n"

    if not courses:
        text += "❌ Hozircha kurslar yo'q.\n\n➕ Yangi kurs qo'shish uchun tugmani bosing."
    else:
        for i, course in enumerate(courses, 1):
            status = "✅" if course['is_active'] else "⭕"
            price_text = await format_price(course['price'])
            text += f"{i}. {status} <b>{course['name']}</b> - {price_text} so'm\n"

        if active_course:
            text += f"\n🎯 <b>Aktiv kurs:</b> {active_course['name']}"
        else:
            text += "\n⚠️ <b>Aktiv kurs tanlanmagan!</b>"

    await query.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_courses_keyboard(courses)
    )


@admin_required_callback
async def add_course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi kurs qo'shish - boshlash"""
    query = update.callback_query
    await query.answer()

    context.user_data['state'] = 'waiting_course_name'
    context.user_data['new_course'] = {}

    await query.message.edit_text(
        text="📝 <b>Yangi kurs qo'shish</b>\n\n"
             "1️⃣ Kurs nomini kiriting:\n\n"
             "Misol: <code>2026-yilga Qadam</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_COURSE_NAME


async def receive_course_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kurs nomi"""
    if context.user_data.get('state') != 'waiting_course_name':
        return

    name = update.message.text.strip()
    context.user_data['new_course']['name'] = name
    context.user_data['state'] = 'waiting_course_price'

    await update.message.reply_text(
        text=f"✅ Kurs nomi: <b>{name}</b>\n\n"
             "2️⃣ Narxni kiriting (so'mda):\n\n"
             "Misol: <code>97000</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_COURSE_PRICE


async def receive_course_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kurs narxi"""
    if context.user_data.get('state') != 'waiting_course_price':
        return

    text = update.message.text.strip().replace(" ", "")

    if not text.isdigit():
        await update.message.reply_text(
            text="❌ Iltimos, faqat raqam kiriting!\n\nMisol: <code>97000</code>",
            parse_mode='HTML',
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_COURSE_PRICE

    price = int(text) * 100  # So'm -> Tiyin
    context.user_data['new_course']['price'] = price
    context.user_data['state'] = 'waiting_course_channel_id'

    await update.message.reply_text(
        text=f"✅ Narx: <b>{text}</b> so'm\n\n"
             "3️⃣ Yopiq kanal ID kiriting:\n\n"
             "Misol: <code>-1001234567890</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_COURSE_CHANNEL_ID


async def receive_course_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal ID"""
    if context.user_data.get('state') != 'waiting_course_channel_id':
        return

    channel_id = update.message.text.strip()
    context.user_data['new_course']['channel_id'] = channel_id
    context.user_data['state'] = 'waiting_course_channel_url'

    await update.message.reply_text(
        text=f"✅ Kanal ID: <code>{channel_id}</code>\n\n"
             "4️⃣ Yopiq kanal linkini kiriting:\n\n"
             "Misol: <code>https://t.me/+abc123</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_COURSE_CHANNEL_URL


async def receive_course_channel_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal URL"""
    if context.user_data.get('state') != 'waiting_course_channel_url':
        return

    channel_url = update.message.text.strip()
    context.user_data['new_course']['channel_url'] = channel_url
    context.user_data['state'] = 'waiting_course_welcome_text'

    await update.message.reply_text(
        text=f"✅ Kanal link: {channel_url}\n\n"
             "5️⃣ Welcome matnini kiriting:\n\n"
             "Bu matn foydalanuvchi /start bosganida ko'rinadi.\n"
             "HTML formatda yozishingiz mumkin.",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_COURSE_WELCOME_TEXT


async def receive_course_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome matn"""
    if context.user_data.get('state') != 'waiting_course_welcome_text':
        return

    welcome_text = update.message.text
    course_data = context.user_data['new_course']

    # Kursni yaratish
    course_id = await create_course(
        name=course_data['name'],
        price=course_data['price'],
        channel_id=course_data['channel_id'],
        channel_url=course_data['channel_url'],
        welcome_text=welcome_text
    )

    price_text = await format_price(course_data['price'])

    await update.message.reply_text(
        text=f"✅ <b>Kurs muvaffaqiyatli yaratildi!</b>\n\n"
             f"📚 <b>Nomi:</b> {course_data['name']}\n"
             f"💰 <b>Narx:</b> {price_text} so'm\n"
             f"📢 <b>Kanal:</b> {course_data['channel_url']}\n\n"
             f"⚠️ Kursni aktivlashtirish uchun kurslar ro'yxatidan tanlang.",
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )

    context.user_data.clear()
    return ConversationHandler.END


@admin_required_callback
async def course_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kurs tafsilotlari"""
    query = update.callback_query
    await query.answer()

    # callback_data: course_detail_123
    course_id = int(query.data.split("_")[2])
    course = await get_course(course_id)

    if not course:
        await query.message.edit_text(
            text="❌ Kurs topilmadi!",
            reply_markup=get_back_keyboard()
        )
        return

    status = "✅ Aktiv" if course['is_active'] else "⭕ Noaktiv"
    price_text = await format_price(course['price'])

    text = (
        f"📚 <b>{course['name']}</b>\n\n"
        f"📊 <b>Status:</b> {status}\n"
        f"💰 <b>Narx:</b> {price_text} so'm\n"
        f"📢 <b>Kanal ID:</b> <code>{course['channel_id']}</code>\n"
        f"🔗 <b>Kanal URL:</b> {course['channel_url'] or '-'}\n"
        f"📅 <b>Yaratilgan:</b> {course['created_at']}\n\n"
        f"📝 <b>Welcome matn:</b>\n"
        f"<i>{course['welcome_text'][:200] + '...' if course['welcome_text'] and len(course['welcome_text']) > 200 else course['welcome_text'] or '-'}</i>"
    )

    await query.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_course_detail_keyboard(course_id, course['is_active'])
    )


@admin_required_callback
async def activate_course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kursni aktivlashtirish"""
    query = update.callback_query

    # callback_data: activate_course_123
    course_id = int(query.data.split("_")[2])

    await set_active_course(course_id)
    course = await get_course(course_id)

    await query.answer(f"✅ {course['name']} aktivlashtirildi!", show_alert=True)

    # Kurslar menyusiga qaytish
    await courses_menu_callback(update, context)


@admin_required_callback
async def delete_course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kursni o'chirish"""
    query = update.callback_query

    # callback_data: delete_course_123
    course_id = int(query.data.split("_")[2])
    course = await get_course(course_id)

    if course['is_active']:
        await query.answer("❌ Aktiv kursni o'chirib bo'lmaydi!", show_alert=True)
        return

    await delete_course(course_id)
    await query.answer(f"🗑️ {course['name']} o'chirildi!", show_alert=True)

    # Kurslar menyusiga qaytish
    await courses_menu_callback(update, context)


@admin_required_callback
async def edit_course_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kursni tahrirlash menyusi"""
    query = update.callback_query
    await query.answer()

    # callback_data: edit_course_123
    course_id = int(query.data.split("_")[2])
    course = await get_course(course_id)

    if not course:
        await query.message.edit_text(
            text="❌ Kurs topilmadi!",
            reply_markup=get_back_keyboard()
        )
        return

    context.user_data['edit_course_id'] = course_id

    await query.message.edit_text(
        text=f"✏️ <b>{course['name']}</b> - Tahrirlash\n\n"
             f"Qaysi maydonni o'zgartirmoqchisiz?",
        parse_mode='HTML',
        reply_markup=get_course_edit_keyboard(course_id)
    )


@admin_required_callback
async def edit_course_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kurs nomini tahrirlash"""
    query = update.callback_query
    await query.answer()

    course_id = context.user_data.get('edit_course_id')
    context.user_data['state'] = 'waiting_edit_name'

    await query.message.edit_text(
        text="📝 Yangi kurs nomini kiriting:",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_EDIT_NAME


async def receive_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi nom"""
    if context.user_data.get('state') != 'waiting_edit_name':
        return

    course_id = context.user_data.get('edit_course_id')
    new_name = update.message.text.strip()

    await update_course(course_id, name=new_name)

    await update.message.reply_text(
        text=f"✅ Kurs nomi yangilandi: <b>{new_name}</b>",
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )

    context.user_data.clear()
    return ConversationHandler.END


@admin_required_callback
async def edit_course_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kurs narxini tahrirlash"""
    query = update.callback_query
    await query.answer()

    course_id = context.user_data.get('edit_course_id')
    context.user_data['state'] = 'waiting_edit_price'

    await query.message.edit_text(
        text="💰 Yangi narxni kiriting (so'mda):\n\nMisol: <code>97000</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_EDIT_PRICE


async def receive_edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi narx"""
    if context.user_data.get('state') != 'waiting_edit_price':
        return

    text = update.message.text.strip().replace(" ", "")

    if not text.isdigit():
        await update.message.reply_text(
            text="❌ Iltimos, faqat raqam kiriting!",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_EDIT_PRICE

    course_id = context.user_data.get('edit_course_id')
    new_price = int(text) * 100  # So'm -> Tiyin

    await update_course(course_id, price=new_price)

    await update.message.reply_text(
        text=f"✅ Kurs narxi yangilandi: <b>{text}</b> so'm",
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )

    context.user_data.clear()
    return ConversationHandler.END


@admin_required_callback
async def edit_course_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal ID tahrirlash"""
    query = update.callback_query
    await query.answer()

    context.user_data['state'] = 'waiting_edit_channel_id'

    await query.message.edit_text(
        text="📢 Yangi kanal ID kiriting:\n\nMisol: <code>-1001234567890</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_EDIT_CHANNEL_ID


async def receive_edit_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi kanal ID"""
    if context.user_data.get('state') != 'waiting_edit_channel_id':
        return

    course_id = context.user_data.get('edit_course_id')
    new_channel_id = update.message.text.strip()

    await update_course(course_id, channel_id=new_channel_id)
    context.user_data['state'] = 'waiting_edit_channel_url'

    await update.message.reply_text(
        text=f"✅ Kanal ID yangilandi!\n\n🔗 Endi kanal URL kiriting:\n\nMisol: <code>https://t.me/+abc123</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_EDIT_CHANNEL_URL


async def receive_edit_channel_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi kanal URL"""
    if context.user_data.get('state') != 'waiting_edit_channel_url':
        return

    course_id = context.user_data.get('edit_course_id')
    new_channel_url = update.message.text.strip()

    await update_course(course_id, channel_url=new_channel_url)

    await update.message.reply_text(
        text=f"✅ Kanal URL yangilandi: {new_channel_url}",
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )

    context.user_data.clear()
    return ConversationHandler.END


@admin_required_callback
async def edit_course_welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome matnni tahrirlash"""
    query = update.callback_query
    await query.answer()

    context.user_data['state'] = 'waiting_edit_welcome_text'

    await query.message.edit_text(
        text="📝 Yangi welcome matnini kiriting:\n\n"
             "HTML formatda yozishingiz mumkin.",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_EDIT_WELCOME_TEXT


async def receive_edit_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi welcome matn"""
    if context.user_data.get('state') != 'waiting_edit_welcome_text':
        return

    course_id = context.user_data.get('edit_course_id')
    new_welcome_text = update.message.text

    await update_course(course_id, welcome_text=new_welcome_text)

    await update.message.reply_text(
        text="✅ Welcome matn yangilandi!",
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )

    context.user_data.clear()
    return ConversationHandler.END