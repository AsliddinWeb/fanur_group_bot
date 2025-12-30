import aiosqlite
from config import DB_PATH
from datetime import datetime


async def create_payment(chat_id: int, screenshot_file_id: str, amount: int = 97000) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO payments (chat_id, amount, screenshot_file_id, status)
            VALUES (?, ?, ?, 'pending')
        ''', (chat_id, amount, screenshot_file_id))
        await db.commit()
        return cursor.lastrowid


async def get_payment(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM payments WHERE id = ?', (payment_id,)) as cursor:
            return await cursor.fetchone()


async def get_pending_payments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT * FROM payments WHERE status = 'pending' ORDER BY created_at DESC
        ''') as cursor:
            return await cursor.fetchall()


async def get_user_payments(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT * FROM payments WHERE chat_id = ? ORDER BY created_at DESC
        ''', (chat_id,)) as cursor:
            return await cursor.fetchall()


async def confirm_payment(payment_id: int, confirmed_by: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            UPDATE payments 
            SET status = 'confirmed', confirmed_at = ?, confirmed_by = ?
            WHERE id = ? AND status = 'pending'
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), confirmed_by, payment_id))
        await db.commit()
        return cursor.rowcount > 0


async def reject_payment(payment_id: int, confirmed_by: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            UPDATE payments 
            SET status = 'rejected', confirmed_at = ?, confirmed_by = ?
            WHERE id = ? AND status = 'pending'
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), confirmed_by, payment_id))
        await db.commit()
        return cursor.rowcount > 0


async def get_payment_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        # Jami to'lovlar
        async with db.execute('SELECT COUNT(*) FROM payments') as cursor:
            total = (await cursor.fetchone())[0]

        # Tasdiqlangan
        async with db.execute('SELECT COUNT(*) FROM payments WHERE status = "confirmed"') as cursor:
            confirmed = (await cursor.fetchone())[0]

        # Kutilayotgan
        async with db.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"') as cursor:
            pending = (await cursor.fetchone())[0]

        # Rad etilgan
        async with db.execute('SELECT COUNT(*) FROM payments WHERE status = "rejected"') as cursor:
            rejected = (await cursor.fetchone())[0]

        # Jami summa (tasdiqlangan)
        async with db.execute('SELECT SUM(amount) FROM payments WHERE status = "confirmed"') as cursor:
            total_amount = (await cursor.fetchone())[0] or 0

        return {
            'total': total,
            'confirmed': confirmed,
            'pending': pending,
            'rejected': rejected,
            'total_amount': total_amount
        }


async def has_confirmed_payment(chat_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM payments WHERE chat_id = ? AND status = 'confirmed'
        ''', (chat_id,)) as cursor:
            count = (await cursor.fetchone())[0]
            return count > 0