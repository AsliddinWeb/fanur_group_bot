import base64
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    CHANNEL_URL,
    ADMIN_USERNAME,
    PAYME_MERCHANT_ID,
    PAYME_TEST_MODE,
    PAYME_CHECKOUT_URL,
    PAYME_TEST_CHECKOUT_URL,
    BOT_USERNAME
)


def get_payme_checkout_url(user_id: int, course_id: int, amount: int) -> str:
    """Payme checkout URL yaratish (base64 encoded)"""
    # Callback URL (to'lovdan keyin qaytish)
    callback_url = f"https://t.me/{BOT_USERNAME}?start=after_payment"

    # Base64 uchun string (course_id ham qo'shildi)
    params = f"m={PAYME_MERCHANT_ID};ac.user_id={user_id};ac.course_id={course_id};a={amount};c={callback_url}"

    # Base64 encode
    encoded = base64.b64encode(params.encode()).decode()

    # Test yoki production
    base_url = PAYME_TEST_CHECKOUT_URL if PAYME_TEST_MODE else PAYME_CHECKOUT_URL

    return f"{base_url}/{encoded}"


def get_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga qo'shilish", url=CHANNEL_URL)]
    ])


def get_check_subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga qo'shilish", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")]
    ])


def get_payment_keyboard(user_id: int, course_id: int, amount: int) -> InlineKeyboardMarkup:
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    payme_url = get_payme_checkout_url(user_id, course_id, amount)

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Payme orqali to'lash", url=payme_url)],
        [
            InlineKeyboardButton("⁉️ Yordam", url=admin_url),
            InlineKeyboardButton("🔍 To'lovlar tarix", callback_data="payment_history")
        ]
    ])


def get_back_to_payment_keyboard(user_id: int, course_id: int = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_payment")]
    ])


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("📚 Kurslar", callback_data="admin_courses")],
        [InlineKeyboardButton("💰 Payme to'lovlar", callback_data="admin_payme")],
        [InlineKeyboardButton("📢 Reklama yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔍 Foydalanuvchi qidirish", callback_data="admin_search")],
        [InlineKeyboardButton("📥 Export", callback_data="admin_export")],
        [InlineKeyboardButton("👥 Adminlar", callback_data="admin_manage")],
        [InlineKeyboardButton("⚙️ Majburiy obuna", callback_data="admin_subscription")]
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ])


def get_subscription_settings_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "❌ O'chirish" if is_enabled else "✅ Yoqish"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data="toggle_subscription")],
        [InlineKeyboardButton("📝 Kanal o'zgartirish", callback_data="change_channel")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ])


def get_admin_manage_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Admin qo'shish", callback_data="add_admin")],
        [InlineKeyboardButton("➖ Admin o'chirish", callback_data="remove_admin")],
        [InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data="list_admins")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ])


def get_export_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 CSV", callback_data="export_csv")],
        [InlineKeyboardButton("📊 Excel", callback_data="export_excel")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ])


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]
    ])


def get_payme_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Payme statistikasi", callback_data="payme_stats")],
        [InlineKeyboardButton("📋 Oxirgi to'lovlar", callback_data="payme_recent")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ])


# ============ KURSLAR UCHUN YANGI KLAVIATURALAR ============

def get_courses_keyboard(courses: list) -> InlineKeyboardMarkup:
    """Kurslar ro'yxati klaviaturasi"""
    keyboard = []

    for course in courses:
        status = "✅" if course['is_active'] else "⭕"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {course['name']}",
                callback_data=f"course_detail_{course['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton("➕ Yangi kurs", callback_data="add_course")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")])

    return InlineKeyboardMarkup(keyboard)


def get_course_detail_keyboard(course_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Kurs tafsilotlari klaviaturasi"""
    keyboard = []

    if not is_active:
        keyboard.append([
            InlineKeyboardButton("✅ Aktivlashtirish", callback_data=f"activate_course_{course_id}")
        ])

    keyboard.append([
        InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_course_{course_id}")
    ])

    if not is_active:
        keyboard.append([
            InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_course_{course_id}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_courses")])

    return InlineKeyboardMarkup(keyboard)


def get_course_edit_keyboard(course_id: int) -> InlineKeyboardMarkup:
    """Kurs tahrirlash klaviaturasi"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Nom", callback_data=f"edit_name_{course_id}")],
        [InlineKeyboardButton("💰 Narx", callback_data=f"edit_price_{course_id}")],
        [InlineKeyboardButton("📢 Kanal", callback_data=f"edit_channel_{course_id}")],
        [InlineKeyboardButton("📄 Welcome matn", callback_data=f"edit_welcome_{course_id}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data=f"course_detail_{course_id}")]
    ])