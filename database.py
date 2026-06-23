import os
import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

_db_initialized = False


async def init_db():
    global _db_initialized

    if _db_initialized:
        return

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except asyncpg.InvalidPasswordError:
        raise RuntimeError("Database authentication failed: invalid credentials")
    except asyncpg.CannotConnectNowError:
        raise RuntimeError("Database is not ready to accept connections. Try again shortly.")
    except OSError as e:
        raise RuntimeError(f"Could not reach the database host: {str(e)}")
    except asyncpg.PostgresError as e:
        raise RuntimeError(f"Failed to connect to the database: {str(e)}")

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
    except asyncpg.PostgresError as e:
        raise RuntimeError(f"Failed to initialize database tables: {str(e)}")
    finally:
        await conn.close()

    _db_initialized = True


@asynccontextmanager
async def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    await init_db()

    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except asyncpg.InvalidPasswordError:
        raise RuntimeError("Database authentication failed: invalid credentials")
    except asyncpg.CannotConnectNowError:
        raise RuntimeError("Database is not ready to accept connections. Try again shortly.")
    except OSError as e:
        raise RuntimeError(f"Could not reach the database host: {str(e)}")
    except asyncpg.PostgresError as e:
        raise RuntimeError(f"Failed to connect to the database: {str(e)}")

    try:
        yield conn
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio
    import sys

    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set")
        sys.exit(1)

    try:
        asyncio.run(init_db())
        print("Database initialized successfully")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
