import csv
import os
from openpyxl import Workbook
from services.user_service import get_all_users

EXPORT_DIR = "exports"


def ensure_export_dir():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)


async def export_to_csv() -> str:
    ensure_export_dir()
    filepath = os.path.join(EXPORT_DIR, "users.csv")

    users = await get_all_users()

    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Chat ID', 'Ism', 'Familiya', 'Username', 'Qo\'shilgan sana', 'Aktiv'])

        for user in users:
            writer.writerow([
                user['id'],
                user['chat_id'],
                user['first_name'],
                user['last_name'],
                user['username'],
                user['joined_at'],
                'Ha' if user['is_active'] else 'Yo\'q'
            ])

    return filepath


async def export_to_excel() -> str:
    ensure_export_dir()
    filepath = os.path.join(EXPORT_DIR, "users.xlsx")

    users = await get_all_users()

    wb = Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"

    # Header
    headers = ['ID', 'Chat ID', 'Ism', 'Familiya', 'Username', 'Qo\'shilgan sana', 'Aktiv']
    ws.append(headers)

    # Data
    for user in users:
        ws.append([
            user['id'],
            user['chat_id'],
            user['first_name'],
            user['last_name'],
            user['username'],
            user['joined_at'],
            'Ha' if user['is_active'] else 'Yo\'q'
        ])

    # Ustun kengligini sozlash
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column_letter].width = max_length + 2

    wb.save(filepath)
    return filepath