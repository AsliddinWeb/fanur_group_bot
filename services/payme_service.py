import aiosqlite
import logging
from config import DB_PATH
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


async def create_order(user_id: int, amount: int, course_id: int = None) -> str:
    """Yangi order yaratish"""
    order_id = str(uuid.uuid4().hex)[:16]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO payme_transactions (user_id, order_id, amount, course_id, state)
            VALUES (?, ?, ?, ?, 0)
        ''', (user_id, order_id, amount, course_id))
        await db.commit()
        logger.info(f"Order created: {order_id}, user: {user_id}, course: {course_id}")

    return order_id


async def get_order_by_id(order_id: str):
    """Order ID bo'yicha olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                'SELECT * FROM payme_transactions WHERE order_id = ?',
                (order_id,)
        ) as cursor:
            return await cursor.fetchone()


async def get_order_by_payme_id(payme_transaction_id: str):
    """Payme transaction ID bo'yicha olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                'SELECT * FROM payme_transactions WHERE payme_transaction_id = ?',
                (payme_transaction_id,)
        ) as cursor:
            return await cursor.fetchone()


async def get_user_orders(user_id: int):
    """Foydalanuvchi orderlari"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT * FROM payme_transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,)) as cursor:
            return await cursor.fetchall()


async def update_order_state(order_id: str, state: int, payme_transaction_id: str = None):
    """Order holatini yangilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        if payme_transaction_id:
            await db.execute('''
                UPDATE payme_transactions 
                SET state = ?, payme_transaction_id = ?
                WHERE order_id = ?
            ''', (state, payme_transaction_id, order_id))
        else:
            await db.execute('''
                UPDATE payme_transactions 
                SET state = ?
                WHERE order_id = ?
            ''', (state, order_id))
        await db.commit()


async def set_order_perform_time(order_id: str):
    """To'lov vaqtini belgilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE payme_transactions 
            SET state = 2, perform_time = ?
            WHERE order_id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), order_id))
        await db.commit()


async def set_order_cancel_time(order_id: str, reason: int, state: int = -1):
    """Bekor qilish vaqtini belgilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE payme_transactions 
            SET state = ?, reason = ?, cancel_time = ?
            WHERE order_id = ?
        ''', (state, reason, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), order_id))
        await db.commit()


async def has_successful_payment(user_id: int, course_id: int = None) -> bool:
    """Foydalanuvchi muvaffaqiyatli to'lov qilganmi (kurs bo'yicha)"""
    async with aiosqlite.connect(DB_PATH) as db:
        if course_id:
            async with db.execute('''
                SELECT COUNT(*) FROM payme_transactions 
                WHERE user_id = ? AND course_id = ? AND state = 2
            ''', (user_id, course_id)) as cursor:
                count = (await cursor.fetchone())[0]
        else:
            async with db.execute('''
                SELECT COUNT(*) FROM payme_transactions 
                WHERE user_id = ? AND state = 2
            ''', (user_id,)) as cursor:
                count = (await cursor.fetchone())[0]
        return count > 0


async def get_payme_stats() -> dict:
    """Payme statistikasi"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Jami
        async with db.execute('SELECT COUNT(*) FROM payme_transactions') as cursor:
            total = (await cursor.fetchone())[0]

        # Success
        async with db.execute('SELECT COUNT(*) FROM payme_transactions WHERE state = 2') as cursor:
            success = (await cursor.fetchone())[0]

        # Pending
        async with db.execute('SELECT COUNT(*) FROM payme_transactions WHERE state IN (0, 1)') as cursor:
            pending = (await cursor.fetchone())[0]

        # Cancelled
        async with db.execute('SELECT COUNT(*) FROM payme_transactions WHERE state IN (-1, -2)') as cursor:
            cancelled = (await cursor.fetchone())[0]

        # Jami summa (success)
        async with db.execute('SELECT SUM(amount) FROM payme_transactions WHERE state = 2') as cursor:
            total_amount = (await cursor.fetchone())[0] or 0

        return {
            'total': total,
            'success': success,
            'pending': pending,
            'cancelled': cancelled,
            'total_amount': total_amount
        }


async def get_orders_by_time_range(start_time: int, end_time: int):
    """Vaqt oralig'idagi orderlar (GetStatement uchun)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT * FROM payme_transactions 
            WHERE state = 2
            ORDER BY perform_time
        ''') as cursor:
            return await cursor.fetchall()


async def get_recent_orders(limit: int = 10):
    """Oxirgi orderlar"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT pt.*, c.name as course_name
            FROM payme_transactions pt
            LEFT JOIN courses c ON pt.course_id = c.id
            ORDER BY pt.created_at DESC
            LIMIT ?
        ''', (limit,)) as cursor:
            return await cursor.fetchall()


async def get_pending_order_by_user(user_id: int, course_id: int = None):
    """Foydalanuvchining pending orderini olish (kurs bo'yicha)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if course_id:
            async with db.execute('''
                SELECT * FROM payme_transactions 
                WHERE user_id = ? AND course_id = ? AND state = 1
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id, course_id)) as cursor:
                return await cursor.fetchone()
        else:
            async with db.execute('''
                SELECT * FROM payme_transactions 
                WHERE user_id = ? AND state = 1
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,)) as cursor:
                return await cursor.fetchone()


async def get_course_stats(course_id: int) -> dict:
    """Kurs bo'yicha statistika"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Jami
        async with db.execute('''
            SELECT COUNT(*) FROM payme_transactions WHERE course_id = ?
        ''', (course_id,)) as cursor:
            total = (await cursor.fetchone())[0]

        # Success
        async with db.execute('''
            SELECT COUNT(*) FROM payme_transactions WHERE course_id = ? AND state = 2
        ''', (course_id,)) as cursor:
            success = (await cursor.fetchone())[0]

        # Jami summa
        async with db.execute('''
            SELECT SUM(amount) FROM payme_transactions WHERE course_id = ? AND state = 2
        ''', (course_id,)) as cursor:
            total_amount = (await cursor.fetchone())[0] or 0

        return {
            'total': total,
            'success': success,
            'total_amount': total_amount
        }