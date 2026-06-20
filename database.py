from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "expense.db"

def get_connection():
    return aiosqlite.connect(DB_PATH)


async def init_db():
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute('''CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    item_name TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT,
    payment_method TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
        await cursor.execute('''CREATE TABLE IF NOT EXISTS budgets(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        month TEXT NOT NULL,
                        monthly_limit REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(category, month))

''')
        await cursor.execute('''CREATE TABLE IF NOT EXISTS incomes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    amount REAL NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
        await conn.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())

