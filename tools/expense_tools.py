from mcp_instance import mcp
from database import get_connection
import asyncpg
from datetime import datetime

ALLOWED_COLUMNS = {"date", "item_name", "amount", "category", "payment_method", "notes"}


def _validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _validate_month(month_str: str) -> bool:
    try:
        datetime.strptime(month_str, "%Y-%m")
        return True
    except ValueError:
        return False


@mcp.tool
async def check_tables():
    """
    Debug tool to verify which tables exist in the database.
    """
    try:
        async with get_connection() as conn:
            rows = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
        return {"tables": [row["table_name"] for row in rows]}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def add_expense(date: str, item_name: str, amount: float, category: str,
                      payment_method: str, notes: str = None):
    """
    Add a new expense record to the database.
    """
    if not date or not date.strip():
        return {"error": "Date cannot be empty"}
    if not _validate_date(date):
        return {"error": f"Invalid date format '{date}'. Expected YYYY-MM-DD"}
    if not item_name or not item_name.strip():
        return {"error": "Item name cannot be empty"}
    if amount <= 0:
        return {"error": "Amount must be greater than 0"}
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}
    if not payment_method or not payment_method.strip():
        return {"error": "Payment method cannot be empty"}

    try:
        async with get_connection() as conn:
            await conn.execute('''
                INSERT INTO expenses (date, item_name, amount, category, payment_method, notes)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', date, item_name, amount, category, payment_method, notes)
            return {"message": "Expense added successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def list_expenses():
    """
    Retrieve all expense records from the database.
    """
    try:
        async with get_connection() as conn:
            rows = await conn.fetch('SELECT * FROM expenses')
            if not rows:
                return {"message": "No data found"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expense(expense_id: int):
    """
    Retrieve a single expense record by its unique ID.
    """
    if expense_id <= 0:
        return {"error": "Expense ID must be a positive integer"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('SELECT * FROM expenses WHERE id = $1', expense_id)
            if not rows:
                return {"message": f"No expense found with ID {expense_id}"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def update_expense(expense_id: int, to_update_column: str, to_update_value: str):
    """
    Update a specific field of an existing expense record.
    """
    if expense_id <= 0:
        return {"error": "Expense ID must be a positive integer"}
    if not to_update_column or not to_update_column.strip():
        return {"error": "Column name cannot be empty"}
    if to_update_column not in ALLOWED_COLUMNS:
        return {"error": f"Invalid column: '{to_update_column}'. Must be one of {ALLOWED_COLUMNS}"}
    if to_update_value is None:
        return {"error": "Update value cannot be None"}

    if to_update_column == "date" and not _validate_date(to_update_value):
        return {"error": f"Invalid date format '{to_update_value}'. Expected YYYY-MM-DD"}
    if to_update_column == "amount":
        try:
            if float(to_update_value) <= 0:
                return {"error": "Amount must be greater than 0"}
        except ValueError:
            return {"error": f"Invalid amount value '{to_update_value}'. Must be a number"}

    try:
        async with get_connection() as conn:
            existing = await conn.fetchrow('SELECT id FROM expenses WHERE id = $1', expense_id)
            if not existing:
                return {"error": f"No expense found with ID {expense_id}"}

            query = f"UPDATE expenses SET {to_update_column} = $1 WHERE id = $2"
            await conn.execute(query, to_update_value, expense_id)
            return {"message": "Expense updated successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def delete_expense(expense_id: int):
    """
    Permanently delete an expense record by its unique ID.
    """
    if expense_id <= 0:
        return {"error": "Expense ID must be a positive integer"}

    try:
        async with get_connection() as conn:
            existing = await conn.fetchrow('SELECT id FROM expenses WHERE id = $1', expense_id)
            if not existing:
                return {"error": f"No expense found with ID {expense_id}. Nothing to delete."}

            await conn.execute('DELETE FROM expenses WHERE id = $1', expense_id)
            return {"message": f"Expense {expense_id} deleted successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expenses_by_category(category: str):
    """
    Retrieve all expense records belonging to a specific category.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses WHERE category = $1
            ''', category)
            if not rows:
                return {"message": f"No expenses found for category '{category}'"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expenses_by_date(date: str):
    """
    Retrieve all expense records for a specific date.
    """
    if not date or not date.strip():
        return {"error": "Date cannot be empty"}
    if not _validate_date(date):
        return {"error": f"Invalid date format '{date}'. Expected YYYY-MM-DD"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses WHERE date = $1
            ''', date)
            if not rows:
                return {"message": f"No expenses found for date '{date}'"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expenses_by_date_range(start_date: str, end_date: str):
    """
    Retrieve all expense records within a date range (inclusive).
    """
    if not start_date or not start_date.strip():
        return {"error": "Start date cannot be empty"}
    if not end_date or not end_date.strip():
        return {"error": "End date cannot be empty"}
    if not _validate_date(start_date):
        return {"error": f"Invalid start date format '{start_date}'. Expected YYYY-MM-DD"}
    if not _validate_date(end_date):
        return {"error": f"Invalid end date format '{end_date}'. Expected YYYY-MM-DD"}
    if start_date > end_date:
        return {"error": f"Start date '{start_date}' cannot be after end date '{end_date}'"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses WHERE date >= $1 AND date <= $2
            ''', start_date, end_date)
            if not rows:
                return {"message": f"No expenses found between '{start_date}' and '{end_date}'"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expenses_above_amount(amount: float):
    """
    Retrieve all expense records where amount >= given threshold.
    """
    if amount < 0:
        return {"error": "Amount threshold cannot be negative"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses WHERE amount >= $1
            ''', amount)
            if not rows:
                return {"message": f"No expenses found above amount {amount}"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expenses_below_amount(amount: float):
    """
    Retrieve all expense records where amount <= given threshold.
    """
    if amount < 0:
        return {"error": "Amount threshold cannot be negative"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses WHERE amount <= $1
            ''', amount)
            if not rows:
                return {"message": f"No expenses found below amount {amount}"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_total_expenses():
    """
    Calculate the total sum of all expense amounts.
    """
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow('SELECT SUM(amount) as total FROM expenses')
            if not row or row["total"] is None:
                return {"message": "No expenses found"}
            return {"total": row["total"]}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_total_expenses_by_category(category: str):
    """
    Calculate the total amount spent in a specific category.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}

    try:
        async with get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT SUM(amount) as total FROM expenses WHERE category = $1
            ''', category)
            if not row or row["total"] is None:
                return {"message": f"No expenses found for category '{category}'"}
            return {"category": category, "total": row["total"]}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def expense_count():
    """
    Return the total number of expense records.
    """
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow('SELECT COUNT(*) as count FROM expenses')
            if not row:
                return {"message": "No data found"}
            return {"count": row["count"]}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def average_expense():
    """
    Calculate the average amount across all expense records.
    """
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow('SELECT AVG(amount) as avg FROM expenses')
            if not row or row["avg"] is None:
                return {"message": "No expenses found to average"}
            return {"average": round(row["avg"], 2)}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def top_expense(limit: int):
    """
    Retrieve top N expenses ordered by amount descending.
    """
    if limit <= 0:
        return {"error": "Limit must be a positive integer"}
    if limit > 1000:
        return {"error": "Limit cannot exceed 1000"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses ORDER BY amount DESC LIMIT $1
            ''', limit)
            if not rows:
                return {"message": "No expenses found"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def category_breakdown():
    """
    Retrieve the total amount spent per expense category.
    """
    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT category, SUM(amount) as total
                FROM expenses GROUP BY category
            ''')
            if not rows:
                return {"message": "No expenses found"}
            return [{"category": row["category"], "total": row["total"]} for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def highest_spending_category():
    """
    Identify the expense category with the highest total spending.
    """
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT category, SUM(amount) AS total
                FROM expenses
                GROUP BY category
                ORDER BY total DESC
                LIMIT 1
            ''')
            if not row:
                return {"message": "No expenses found"}
            return {"category": row["category"], "total": row["total"]}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expenses_by_payment_method(payment_method: str):
    """
    Retrieve all expense records by payment method.
    """
    if not payment_method or not payment_method.strip():
        return {"error": "Payment method cannot be empty"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses WHERE payment_method = $1
            ''', payment_method)
            if not rows:
                return {"message": f"No expenses found for payment method '{payment_method}'"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_total_by_payment_method(payment_method: str):
    """
    Calculate the total amount spent using a specific payment method.
    """
    if not payment_method or not payment_method.strip():
        return {"error": "Payment method cannot be empty"}

    try:
        async with get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT COALESCE(SUM(amount), 0) as total
                FROM expenses WHERE payment_method = $1
            ''', payment_method)
            return {
                "payment_method": payment_method,
                "total_spent": row["total"]
            }
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def payment_method_breakdown():
    """
    Return a ranked breakdown of spending and transaction count per payment method.
    """
    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT payment_method, COUNT(*) as transactions, SUM(amount) as total
                FROM expenses
                GROUP BY payment_method
                ORDER BY total DESC
            ''')
            if not rows:
                return {"message": "No expenses found"}
            return [
                {
                    "payment_method": row["payment_method"],
                    "total_transactions": row["transactions"],
                    "total_spent": row["total"]
                }
                for row in rows
            ]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def most_used_payment_method():
    """
    Identify the payment method used most frequently.
    """
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT payment_method, COUNT(*) as transactions
                FROM expenses
                GROUP BY payment_method
                ORDER BY transactions DESC
                LIMIT 1
            ''')
            if not row:
                return {"message": "No expenses found"}
            return {
                "payment_method": row["payment_method"],
                "total_transactions": row["transactions"]
            }
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_expenses_by_category_and_payment_method(category: str, payment_method: str):
    """
    Retrieve all expense records matching both category and payment method.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}
    if not payment_method or not payment_method.strip():
        return {"error": "Payment method cannot be empty"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM expenses
                WHERE category = $1 AND payment_method = $2
            ''', category, payment_method)
            if not rows:
                return {"message": f"No expenses found for category '{category}' with payment method '{payment_method}'"}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def highest_spending_category_by_month(month: str):
    """
    Get highest spending category for a specific month.
    """
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}
    if not _validate_month(month):
        return {"error": f"Invalid month format '{month}'. Expected YYYY-MM"}

    try:
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
                return {"error": f"No expense records found for month '{month}'"}

            return {
                "category": row["category"],
                "total_spent": row["total"]
            }
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
