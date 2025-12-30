import aiosqlite
from config import DB_PATH, OWNER_ID


async def is_admin(chat_id: int) -> bool:
    if chat_id == OWNER_ID:
        return True

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM admins WHERE chat_id = ?', (chat_id,)) as cursor:
            return await cursor.fetchone() is not None


async def add_admin(chat_id: int, added_by: int) -> bool:
    if chat_id == OWNER_ID:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute('''
                INSERT INTO admins (chat_id, added_by) VALUES (?, ?)
            ''', (chat_id, added_by))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def remove_admin(chat_id: int) -> bool:
    if chat_id == OWNER_ID:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('DELETE FROM admins WHERE chat_id = ?', (chat_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM admins') as cursor:
            return await cursor.fetchall()


async def get_admins_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM admins') as cursor:
            result = await cursor.fetchone()
            return result[0] + 1  # +1 for OWNER