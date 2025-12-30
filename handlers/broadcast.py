import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from middlewares.admin_check import admin_required_callback
from keyboards.inline import get_back_keyboard, get_cancel_keyboard
from services.user_service import get_all_users
from config import BROADCAST_DELAY

logger = logging.getLogger(__name__)

# States
WAITING_BROADCAST_CONTENT = 1


@admin_required_callback
async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['state'] = 'waiting_broadcast'

    await query.message.edit_text(
        text="📢 <b>Reklama yuborish</b>\n\n"
             "Yubormoqchi bo'lgan xabaringizni yuboring.\n\n"
             "📝 Matn, 🖼 Rasm, 🎥 Video yoki ↗️ Forward qilishingiz mumkin.",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_BROADCAST_CONTENT


async def receive_broadcast_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'waiting_broadcast':
        return

    message = update.message
    users = await get_all_users()

    total = len(users)
    success = 0
    failed = 0

    logger.info(f"Broadcast started: {total} users")

    progress_message = await message.reply_text(
        f"📤 Yuborilmoqda...\n\n"
        f"✅ Yuborildi: 0\n"
        f"❌ Yuborilmadi: 0\n"
        f"📊 Jami: {total}"
    )

    for user in users:
        try:
            if message.text:
                await context.bot.send_message(
                    chat_id=user['chat_id'],
                    text=message.text,
                    parse_mode='HTML'
                )
            elif message.photo:
                await context.bot.send_photo(
                    chat_id=user['chat_id'],
                    photo=message.photo[-1].file_id,
                    caption=message.caption,
                    parse_mode='HTML'
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=user['chat_id'],
                    video=message.video.file_id,
                    caption=message.caption,
                    parse_mode='HTML'
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=user['chat_id'],
                    document=message.document.file_id,
                    caption=message.caption,
                    parse_mode='HTML'
                )
            elif message.forward_date:
                await message.copy(chat_id=user['chat_id'])

            success += 1
        except Exception as e:
            failed += 1
            logger.debug(f"Broadcast failed for user {user['chat_id']}: {e}")

        # Har 20 ta userda progressni yangilash
        if (success + failed) % 20 == 0:
            try:
                await progress_message.edit_text(
                    f"📤 Yuborilmoqda...\n\n"
                    f"✅ Yuborildi: {success}\n"
                    f"❌ Yuborilmadi: {failed}\n"
                    f"📊 Jami: {total}"
                )
            except:
                pass

        await asyncio.sleep(BROADCAST_DELAY)

    # Yakuniy natija
    await progress_message.edit_text(
        f"✅ <b>Reklama yuborildi!</b>\n\n"
        f"✅ Yuborildi: {success}\n"
        f"❌ Yuborilmadi: {failed}\n"
        f"📊 Jami: {total}",
        parse_mode='HTML'
    )

    logger.info(f"Broadcast finished: success={success}, failed={failed}")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("❌ Bekor qilindi!")

    context.user_data.clear()

    from keyboards.inline import get_admin_panel_keyboard
    await query.message.edit_text(
        text="🔐 <b>Admin Panel</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        parse_mode='HTML',
        reply_markup=get_admin_panel_keyboard()
    )

    return ConversationHandler.END