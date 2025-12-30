import aiosqlite
from config import DB_PATH


async def create_tables():
    async with aiosqlite.connect(DB_PATH) as db:
        # Users jadvali
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # Admins jadvali
        await db.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                added_by INTEGER,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Settings jadvali
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT
            )
        ''')

        # Broadcasts jadvali
        await db.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type TEXT,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_users INTEGER,
                success INTEGER,
                failed INTEGER
            )
        ''')

        # Payments jadvali (karta orqali to'lovlar)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                amount INTEGER DEFAULT 97000,
                status TEXT DEFAULT 'pending',
                screenshot_file_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                confirmed_at DATETIME,
                confirmed_by INTEGER
            )
        ''')

        # Payme transactions jadvali (YANGI)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payme_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_id TEXT UNIQUE NOT NULL,
                payme_transaction_id TEXT,
                amount INTEGER NOT NULL,
                state INTEGER DEFAULT 0,
                reason INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                perform_time DATETIME,
                cancel_time DATETIME
            )
        ''')

        # Default settings
        await db.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES ('force_subscribe', 'off')
        ''')

        await db.commit()