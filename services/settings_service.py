import aiosqlite
from config import DB_PATH

async def get_setting(key: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT value FROM settings WHERE key = ?', (key,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?
        ''', (key, value, value))
        await db.commit()

async def is_force_subscribe_enabled() -> bool:
    value = await get_setting('force_subscribe')
    return value == 'on'

async def enable_force_subscribe():
    await set_setting('force_subscribe', 'on')

async def disable_force_subscribe():
    await set_setting('force_subscribe', 'off')

async def get_channel_id() -> str | None:
    return await get_setting('channel_id')

async def set_channel_id(channel_id: str):
    await set_setting('channel_id', channel_id)