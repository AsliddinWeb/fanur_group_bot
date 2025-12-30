from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("📊 Statistika"), KeyboardButton("📢 Reklama")],
        [KeyboardButton("🔍 Qidirish"), KeyboardButton("📥 Export")],
        [KeyboardButton("👥 Adminlar"), KeyboardButton("⚙️ Sozlamalar")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_broadcast_type_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("📝 Matn"), KeyboardButton("🖼 Rasm")],
        [KeyboardButton("🎥 Video"), KeyboardButton("↗️ Forward")],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()