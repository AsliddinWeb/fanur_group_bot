from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CHANNEL_URL, ADMIN_USERNAME, PAYME_MERCHANT_ID, PAYME_AMOUNT, PAYME_TEST_MODE


def get_payme_checkout_url(user_id: int) -> str:
    """Payme checkout URL yaratish"""
    # Test yoki production
    if PAYME_TEST_MODE:
        base_url = "https://test.payme.uz/checkout"
    else:
        base_url = "https://payme.uz/checkout"

    # URL yaratish
    url = f"{base_url}/{PAYME_MERCHANT_ID}?amount={PAYME_AMOUNT}&account[user_id]={user_id}"

    return url


def get_start_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 Kanalga qo'shilish", url=CHANNEL_URL)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_check_subscription_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 Kanalga qo'shilish", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_keyboard(user_id: int) -> InlineKeyboardMarkup:
    payme_url = get_payme_checkout_url(user_id)

    keyboard = [
        [InlineKeyboardButton("💳 Payme orqali to'lash", url=payme_url)],
        [
            InlineKeyboardButton("⁉️ Yordam", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"),
            InlineKeyboardButton("🔍 To'lovlar tarix", callback_data="payment_history")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_payment_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_payment")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("💰 Payme to'lovlar", callback_data="admin_payme")],
        [InlineKeyboardButton("📢 Reklama yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔍 Foydalanuvchi qidirish", callback_data="admin_search")],
        [InlineKeyboardButton("📥 Export", callback_data="admin_export")],
        [InlineKeyboardButton("👥 Adminlar", callback_data="admin_manage")],
        [InlineKeyboardButton("⚙️ Majburiy obuna", callback_data="admin_subscription")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_subscription_settings_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    status_btn = InlineKeyboardButton(
        "❌ O'chirish" if is_enabled else "✅ Yoqish",
        callback_data="toggle_subscription"
    )
    keyboard = [
        [status_btn],
        [InlineKeyboardButton("📝 Kanal o'zgartirish", callback_data="change_channel")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_manage_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Admin qo'shish", callback_data="add_admin")],
        [InlineKeyboardButton("➖ Admin o'chirish", callback_data="remove_admin")],
        [InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data="list_admins")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_export_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📄 CSV", callback_data="export_csv")],
        [InlineKeyboardButton("📊 Excel", callback_data="export_excel")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payme_stats_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Payme statistikasi", callback_data="payme_stats")],
        [InlineKeyboardButton("📋 Oxirgi to'lovlar", callback_data="payme_recent")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)