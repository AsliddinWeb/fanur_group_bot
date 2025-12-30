import aiosqlite
from config import DB_PATH
from datetime import datetime, timedelta

async def get_daily_stats() -> int:
    today = datetime.now().strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM users WHERE DATE(joined_at) = ?
        ''', (today,)) as cursor:
            result = await cursor.fetchone()
            return result[0]

async def get_weekly_stats() -> int:
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM users WHERE DATE(joined_at) >= ?
        ''', (week_ago,)) as cursor:
            result = await cursor.fetchone()
            return result[0]

async def get_monthly_stats() -> int:
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM users WHERE DATE(joined_at) >= ?
        ''', (month_ago,)) as cursor:
            result = await cursor.fetchone()
            return result[0]

async def get_yearly_stats() -> int:
    year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM users WHERE DATE(joined_at) >= ?
        ''', (year_ago,)) as cursor:
            result = await cursor.fetchone()
            return result[0]

async def get_total_stats() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            result = await cursor.fetchone()
            return result[0]

async def get_active_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM users WHERE is_active = 1') as cursor:
            result = await cursor.fetchone()
            return result[0]

async def get_all_stats() -> dict:
    return {
        'daily': await get_daily_stats(),
        'weekly': await get_weekly_stats(),
        'monthly': await get_monthly_stats(),
        'yearly': await get_yearly_stats(),
        'total': await get_total_stats(),
        'active': await get_active_users_count()
    }