from telegram import Update
from telegram.ext import ContextTypes
from middlewares.admin_check import admin_required_callback
from keyboards.inline import get_export_keyboard, get_back_keyboard
from utils.export_utils import export_to_csv, export_to_excel


@admin_required_callback
async def export_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        text="📥 <b>Export</b>\n\n"
             "Foydalanuvchilar ro'yxatini qaysi formatda yuklab olmoqchisiz?",
        parse_mode='HTML',
        reply_markup=get_export_keyboard()
    )


@admin_required_callback
async def export_csv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("📄 CSV tayyorlanmoqda...")

    try:
        filepath = await export_to_csv()

        await query.message.delete()
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=open(filepath, 'rb'),
            filename="users.csv",
            caption="📄 Foydalanuvchilar ro'yxati (CSV)",
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        await query.message.edit_text(
            text=f"❌ Xatolik yuz berdi: {str(e)}",
            reply_markup=get_back_keyboard()
        )


@admin_required_callback
async def export_excel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("📊 Excel tayyorlanmoqda...")

    try:
        filepath = await export_to_excel()

        await query.message.delete()
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=open(filepath, 'rb'),
            filename="users.xlsx",
            caption="📊 Foydalanuvchilar ro'yxati (Excel)",
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        await query.message.edit_text(
            text=f"❌ Xatolik yuz berdi: {str(e)}",
            reply_markup=get_back_keyboard()
        )