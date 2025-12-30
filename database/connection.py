import aiosqlite
from config import DB_PATH

async def get_db():
    return await aiosqlite.connect(DB_PATH)