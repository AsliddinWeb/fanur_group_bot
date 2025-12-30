from datetime import datetime


def format_user_info(user) -> str:
    is_active = "Ha" if user['is_active'] else "Yo'q"
    username = f"@{user['username']}" if user['username'] else "-"

    return (
        f"👤 <b>Foydalanuvchi ma'lumotlari:</b>\n\n"
        f"🆔 ID: <code>{user['chat_id']}</code>\n"
        f"📛 Ism: {user['first_name'] or '-'}\n"
        f"📝 Familiya: {user['last_name'] or '-'}\n"
        f"🔗 Username: {username}\n"
        f"📅 Qo'shilgan: {user['joined_at']}\n"
        f"✅ Aktiv: {is_active}"
    )


def format_stats(stats: dict) -> str:
    return (
        f"📊 <b>Bot Statistikasi</b>\n\n"
        f"📅 Bugun: <b>{stats['daily']}</b> ta\n"
        f"📆 Hafta: <b>{stats['weekly']}</b> ta\n"
        f"🗓 Oy: <b>{stats['monthly']}</b> ta\n"
        f"📈 Yil: <b>{stats['yearly']}</b> ta\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Jami: <b>{stats['total']}</b> ta\n"
        f"✅ Aktiv: <b>{stats['active']}</b> ta"
    )


def format_admin_info(admin, index: int) -> str:
    return (
        f"{index}. <code>{admin['chat_id']}</code> - "
        f"Qo'shilgan: {admin['added_at']}"
    )


def get_timestamp() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')