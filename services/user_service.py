import aiosqlite
from config import DB_PATH

async def add_user(chat_id: int, first_name: str, last_name: str, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO users (chat_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, first_name, last_name, username))
        await db.commit()

async def get_user(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,)) as cursor:
            return await cursor.fetchone()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE is_active = 1') as cursor:
            return await cursor.fetchall()

async def search_user_by_id(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,)) as cursor:
            return await cursor.fetchone()

async def search_user_by_username(username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE username LIKE ?', (f'%{username}%',)) as cursor:
            return await cursor.fetchall()

async def update_user_status(chat_id: int, is_active: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET is_active = ? WHERE chat_id = ?', (is_active, chat_id))
        await db.commit()

async def get_users_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            result = await cursor.fetchone()
            return result[0]