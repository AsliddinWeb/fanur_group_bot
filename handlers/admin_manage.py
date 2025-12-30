from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from middlewares.admin_check import admin_required_callback
from keyboards.inline import get_admin_manage_keyboard, get_back_keyboard, get_cancel_keyboard
from services.admin_service import add_admin, remove_admin, get_all_admins
from config import OWNER_ID

# States
WAITING_ADD_ADMIN = 1
WAITING_REMOVE_ADMIN = 2


@admin_required_callback
async def admin_manage_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        text="👥 <b>Adminlar boshqaruvi</b>\n\n"
             "Quyidagi amallardan birini tanlang:",
        parse_mode='HTML',
        reply_markup=get_admin_manage_keyboard()
    )


@admin_required_callback
async def add_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Faqat OWNER admin qo'sha oladi
    if query.from_user.id != OWNER_ID:
        await query.answer("⛔️ Faqat bot egasi admin qo'sha oladi!", show_alert=True)
        return

    context.user_data['state'] = 'waiting_add_admin'

    await query.message.edit_text(
        text="➕ <b>Admin qo'shish</b>\n\n"
             "Yangi adminning ID raqamini yuboring.\n\n"
             "Misol: <code>123456789</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_ADD_ADMIN


async def receive_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'waiting_add_admin':
        return

    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(
            text="❌ Iltimos, faqat ID raqam yuboring!",
            reply_markup=get_cancel_keyboard()
        )
        return

    new_admin_id = int(text)
    added_by = update.effective_user.id

    if new_admin_id == OWNER_ID:
        await update.message.reply_text(
            text="❌ Bot egasini admin qilib bo'lmaydi!",
            reply_markup=get_back_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END

    result = await add_admin(new_admin_id, added_by)

    if result:
        await update.message.reply_text(
            text=f"✅ <code>{new_admin_id}</code> admin qilib tayinlandi!",
            parse_mode='HTML',
            reply_markup=get_back_keyboard()
        )
    else:
        await update.message.reply_text(
            text="❌ Bu foydalanuvchi allaqachon admin!",
            reply_markup=get_back_keyboard()
        )

    context.user_data.clear()
    return ConversationHandler.END


@admin_required_callback
async def remove_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Faqat OWNER admin o'chira oladi
    if query.from_user.id != OWNER_ID:
        await query.answer("⛔️ Faqat bot egasi admin o'chira oladi!", show_alert=True)
        return

    context.user_data['state'] = 'waiting_remove_admin'

    await query.message.edit_text(
        text="➖ <b>Admin o'chirish</b>\n\n"
             "O'chirmoqchi bo'lgan adminning ID raqamini yuboring.\n\n"
             "Misol: <code>123456789</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_REMOVE_ADMIN


async def receive_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'waiting_remove_admin':
        return

    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(
            text="❌ Iltimos, faqat ID raqam yuboring!",
            reply_markup=get_cancel_keyboard()
        )
        return

    admin_id = int(text)

    result = await remove_admin(admin_id)

    if result:
        await update.message.reply_text(
            text=f"✅ <code>{admin_id}</code> adminlikdan o'chirildi!",
            parse_mode='HTML',
            reply_markup=get_back_keyboard()
        )
    else:
        await update.message.reply_text(
            text="❌ Bu foydalanuvchi admin emas!",
            reply_markup=get_back_keyboard()
        )

    context.user_data.clear()
    return ConversationHandler.END


@admin_required_callback
async def list_admins_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admins = await get_all_admins()

    text = "📋 <b>Adminlar ro'yxati</b>\n\n"
    text += f"👑 <code>{OWNER_ID}</code> - Bot egasi\n"

    if admins:
        for i, admin in enumerate(admins, 1):
            text += f"{i}. <code>{admin['chat_id']}</code> - Qo'shilgan: {admin['added_at']}\n"

    text += f"\n📊 Jami: {len(admins) + 1} ta admin"

    await query.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard()
    )