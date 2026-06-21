from mcp_instance import mcp
from database import get_connection

ALLOWED_COLUMNS = {"date", "item_name", "amount", "category", "payment_method", "notes"}


@mcp.tool
async def check_tables():
    """
    Debug tool to verify which tables exist in the database.
    """
    async with get_connection() as conn:
        rows = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
    return {
        "tables": [row["table_name"] for row in rows]
    }


@mcp.tool
async def add_expense(date: str, item_name: str, amount: float, category: str,
                      payment_method: str, notes: str = None):
    """
    Add a new expense record to the database.
    """
    async with get_connection() as conn:
        await conn.execute('''
            INSERT INTO expenses (date, item_name, amount, category, payment_method, notes)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', date, item_name, amount, category, payment_method, notes)
        return {"message": "Expense added successfully"}


@mcp.tool
async def list_expenses():
    """
    Retrieve all expense records from the database.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('SELECT * FROM expenses')
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def get_expense(expense_id: int):
    """
    Retrieve a single expense record by its unique ID.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('SELECT * FROM expenses WHERE id = $1', expense_id)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def update_expense(expense_id: int, to_update_column: str, to_update_value: str):
    """
    Update a specific field of an existing expense record.
    """
    if to_update_column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column: '{to_update_column}'. Must be one of {ALLOWED_COLUMNS}")

    async with get_connection() as conn:
        query = f"UPDATE expenses SET {to_update_column} = $1 WHERE id = $2"
        await conn.execute(query, to_update_value, expense_id)
        return {"message": "Expense updated successfully"}


@mcp.tool
async def delete_expense(expense_id: int):
    """
    Permanently delete an expense record by its unique ID.
    """
    async with get_connection() as conn:
        await conn.execute('DELETE FROM expenses WHERE id = $1', expense_id)
        return {"message": f"Expense {expense_id} deleted successfully"}


@mcp.tool
async def get_expenses_by_category(category: str):
    """
    Retrieve all expense records belonging to a specific category.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses WHERE category = $1
        ''', category)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def get_expenses_by_date(date: str):
    """
    Retrieve all expense records for a specific date.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses WHERE date = $1
        ''', date)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def get_expenses_by_date_range(start_date: str, end_date: str):
    """
    Retrieve all expense records within a date range (inclusive).
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses WHERE date >= $1 AND date <= $2
        ''', start_date, end_date)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def get_expenses_above_amount(amount: float):
    """
    Retrieve all expense records where amount >= given threshold.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses WHERE amount >= $1
        ''', amount)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def get_expenses_below_amount(amount: float):
    """
    Retrieve all expense records where amount <= given threshold.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses WHERE amount <= $1
        ''', amount)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def get_total_expenses():
    """
    Calculate the total sum of all expense amounts.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow('SELECT SUM(amount) as total FROM expenses')
        if not row or row["total"] is None:
            return {"message": "No data found"}
        return {"total": row["total"]}


@mcp.tool
async def get_total_expenses_by_category(category: str):
    """
    Calculate the total amount spent in a specific category.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow('''
            SELECT SUM(amount) as total FROM expenses WHERE category = $1
        ''', category)
        if not row or row["total"] is None:
            return {"message": "No data found"}
        return {"category": category, "total": row["total"]}


@mcp.tool
async def expense_count():
    """
    Return the total number of expense records.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow('SELECT COUNT(*) as count FROM expenses')
        if not row:
            return {"message": "No data found"}
        return {"count": row["count"]}


@mcp.tool
async def average_expense():
    """
    Calculate the average amount across all expense records.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow('SELECT AVG(amount) as avg FROM expenses')
        if not row or row["avg"] is None:
            return {"message": "No data found"}
        return {"average": round(row["avg"], 2)}


@mcp.tool
async def top_expense(limit: int):
    """
    Retrieve top N expenses ordered by amount descending.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses ORDER BY amount DESC LIMIT $1
        ''', limit)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def category_breakdown():
    """
    Retrieve the total amount spent per expense category.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT category, SUM(amount) as total
            FROM expenses GROUP BY category
        ''')
        if not rows:
            return {"message": "No data found"}
        return [{"category": row["category"], "total": row["total"]} for row in rows]


@mcp.tool
async def highest_spending_category():
    """
    Identify the expense category with the highest total spending.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow('''
            SELECT category, SUM(amount) AS total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        ''')
        if not row:
            return {"message": "No data found"}
        return {"category": row["category"], "total": row["total"]}


@mcp.tool
async def get_expenses_by_payment_method(payment_method: str):
    """
    Retrieve all expense records by payment method.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses WHERE payment_method = $1
        ''', payment_method)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def get_total_by_payment_method(payment_method: str):
    """
    Calculate the total amount spent using a specific payment method.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses WHERE payment_method = $1
        ''', payment_method)
        return {
            "payment_method": payment_method,
            "total_spent": row["total"]
        }


@mcp.tool
async def payment_method_breakdown():
    """
    Return a ranked breakdown of spending and transaction count per payment method.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT payment_method, COUNT(*) as transactions, SUM(amount) as total
            FROM expenses
            GROUP BY payment_method
            ORDER BY total DESC
        ''')
        if not rows:
            return {"message": "No data found"}
        return [
            {
                "payment_method": row["payment_method"],
                "total_transactions": row["transactions"],
                "total_spent": row["total"]
            }
            for row in rows
        ]


@mcp.tool
async def most_used_payment_method():
    """
    Identify the payment method used most frequently.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow('''
            SELECT payment_method, COUNT(*) as transactions
            FROM expenses
            GROUP BY payment_method
            ORDER BY transactions DESC
            LIMIT 1
        ''')
        if not row:
            return {"message": "No data found"}
        return {
            "payment_method": row["payment_method"],
            "total_transactions": row["transactions"]
        }


@mcp.tool
async def get_expenses_by_category_and_payment_method(category: str, payment_method: str):
    """
    Retrieve all expense records matching both category and payment method.
    """
    async with get_connection() as conn:
        rows = await conn.fetch('''
            SELECT * FROM expenses
            WHERE category = $1 AND payment_method = $2
        ''', category, payment_method)
        if not rows:
            return {"message": "No data found"}
        return [dict(row) for row in rows]


@mcp.tool
async def highest_spending_category_by_month(month: str):
    """
    Get highest spending category for a specific month.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE date LIKE $1
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        """, f"{month}%")

        if not row:
            return {"error": "No expense records found for this month"}

        return {
            "category": row["category"],
            "total_spent": row["total"]
        }
