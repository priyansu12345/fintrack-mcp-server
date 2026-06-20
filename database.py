import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite


def _is_writable(directory: Path) -> bool:
    """Return whether SQLite can create files in *directory*."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=directory):
            pass
        return True
    except OSError:
        return False


def _database_path() -> Path:
    configured_path = os.getenv("FINTRACK_DB_PATH")
    if configured_path:
        path = Path(configured_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    local_data_dir = Path(__file__).resolve().parent / "data"
    if _is_writable(local_data_dir):
        return local_data_dir / "expense.db"

    # Deployed application directories (including Horizon) may be read-only.
    temporary_data_dir = Path(tempfile.gettempdir()) / "fintrack"
    temporary_data_dir.mkdir(parents=True, exist_ok=True)
    return temporary_data_dir / "expense.db"


DB_PATH = _database_path()
_db_initialized = False


def _connect():
    return aiosqlite.connect(str(DB_PATH))


async def init_db():
    global _db_initialized

    if _db_initialized and DB_PATH.exists():
        return

    async with _connect() as conn:
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
        _db_initialized = True


@asynccontextmanager
async def get_connection():
    await init_db()
    async with _connect() as conn:
        yield conn


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
