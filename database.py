import os
import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

_db_initialized = False

async def init_db():
    global _db_initialized
    if _db_initialized:
        return

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses(
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                item_name TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                payment_method TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS budgets(
                id SERIAL PRIMARY KEY,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, month)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS incomes(
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                source TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    finally:
        await conn.close()
    
    _db_initialized = True

@asynccontextmanager
async def get_connection():
    await init_db()
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
