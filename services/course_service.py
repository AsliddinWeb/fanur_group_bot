import aiosqlite
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)


async def create_course(
        name: str,
        price: int,
        channel_id: str,
        channel_url: str = None,
        description: str = None,
        welcome_text: str = None
) -> int:
    """Yangi kurs yaratish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO courses (name, description, welcome_text, price, channel_id, channel_url, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (name, description, welcome_text, price, channel_id, channel_url))
        await db.commit()
        logger.info(f"Course created: {name}")
        return cursor.lastrowid


async def get_course(course_id: int):
    """Kursni ID bo'yicha olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)) as cursor:
            return await cursor.fetchone()


async def get_active_course():
    """Aktiv kursni olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM courses WHERE is_active = 1 LIMIT 1') as cursor:
            return await cursor.fetchone()


async def get_all_courses():
    """Barcha kurslar ro'yxati"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM courses ORDER BY created_at DESC') as cursor:
            return await cursor.fetchall()


async def update_course(
        course_id: int,
        name: str = None,
        description: str = None,
        welcome_text: str = None,
        price: int = None,
        channel_id: str = None,
        channel_url: str = None
) -> bool:
    """Kursni yangilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        updates = []
        values = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if welcome_text is not None:
            updates.append("welcome_text = ?")
            values.append(welcome_text)
        if price is not None:
            updates.append("price = ?")
            values.append(price)
        if channel_id is not None:
            updates.append("channel_id = ?")
            values.append(channel_id)
        if channel_url is not None:
            updates.append("channel_url = ?")
            values.append(channel_url)

        if not updates:
            return False

        values.append(course_id)
        query = f"UPDATE courses SET {', '.join(updates)} WHERE id = ?"

        cursor = await db.execute(query, values)
        await db.commit()
        logger.info(f"Course updated: {course_id}")
        return cursor.rowcount > 0


async def set_active_course(course_id: int) -> bool:
    """Kursni aktiv qilish (boshqalarini o'chirish)"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Avval barcha kurslarni noaktiv qilish
        await db.execute('UPDATE courses SET is_active = 0')

        # Tanlangan kursni aktiv qilish
        cursor = await db.execute('UPDATE courses SET is_active = 1 WHERE id = ?', (course_id,))
        await db.commit()
        logger.info(f"Active course set: {course_id}")
        return cursor.rowcount > 0


async def deactivate_all_courses() -> bool:
    """Barcha kurslarni noaktiv qilish"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE courses SET is_active = 0')
        await db.commit()
        logger.info("All courses deactivated")
        return True


async def delete_course(course_id: int) -> bool:
    """Kursni o'chirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        await db.commit()
        logger.info(f"Course deleted: {course_id}")
        return cursor.rowcount > 0


async def get_courses_count() -> int:
    """Kurslar sonini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM courses') as cursor:
            result = await cursor.fetchone()
            return result[0]


async def format_price(price: int) -> str:
    """Narxni formatlash (tiyin -> so'm)"""
    som = price // 100
    return f"{som:,}".replace(",", " ")