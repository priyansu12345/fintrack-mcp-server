from mcp_instance import mcp
from database import get_connection


@mcp.resource('expense://summary')
async def get_total_expenses():
    """
    MCP resource that provides a full financial summary of all recorded expenses.

    Resource URI:
        expense://summary

    Aggregates three pieces of information in a single query pass:
    the overall total spend, a per-category spending breakdown ranked by
    highest spend, and the total number of transactions recorded.

    Returns:
        dict: A summary report containing:
            - total_expenses (float): Cumulative sum of all expense amounts.
                                    Returns 0.0 if no records exist.
            - total_transactions (int): Total number of expense records in the database.
            - category_breakdown (list[dict]): Per-category totals, each entry containing:
                - category (str): The expense category name.
                - total (float): Total amount spent in that category.
              Ordered by total spend descending. Empty list if no records exist.

    Example:
        # Accessing expense://summary returns:
        {
            "total_expenses": 12500.0,
            "total_transactions": 37,
            "category_breakdown": [
                {"category": "Food", "total": 4200.0},
                {"category": "Transport", "total": 1800.0},
                {"category": "Utilities", "total": 950.0}
            ]
        }
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
        """)
        total = (await cursor.fetchone())[0]

        await cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
        """)
        category_breakdown = [
            {"category": row[0], "total": row[1]}
            for row in await cursor.fetchall()
        ]

        await cursor.execute("""
            SELECT COUNT(*)
            FROM expenses
        """)
        total_transactions = (await cursor.fetchone())[0]

        return {
            "total_expenses": total,
            "total_transactions": total_transactions,
            "category_breakdown": category_breakdown
        }


@mcp.resource('expense://count')
async def expense_count():
    """
    MCP resource that returns the total number of expense records in the database.

    Resource URI:
        expense://count

    Returns:
        dict: A single-key report containing:
            - expense_count (int): The total number of expense records.
                                   Returns 0 if no records exist.

    Example:
        # Accessing expense://count returns:
        {"expense_count": 37}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT COUNT(*)
            FROM expenses
        ''')
        rows = await cursor.fetchone()
        count = rows[0]
        return {
            "expense_count": count
        }


@mcp.resource('expense://monthly/{month}')
async def get_monthly_expenses(month: str):
    """
    MCP resource that provides a spending summary for a specific month.

    Resource URI:
        expense://monthly/{month}

    Filters expenses by matching the date column against the given month prefix
    using a LIKE query (e.g., '2024-06%'), so all dates within that month are included.

    Args:
        month (str): The target month in 'YYYY-MM' format (e.g., '2024-06').

    Returns:
        dict: A monthly summary containing:
            - month (str): The queried month as provided.
            - total (float): Total amount spent during the month.
                            Returns 0.0 if no expenses exist for that month.
            - total_transactions (int): Number of expense records in that month.
            - category_breakdown (list[dict]): Per-category totals for the month,
            each entry containing:
                - category (str): The expense category name.
                - total (float): Amount spent in that category during the month.
            Ordered by total spend descending. Empty list if no records exist.

    Example:
        # Accessing expense://monthly/2024-06 returns:
        {
            "month": "2024-06",
            "total": 3200.0,
            "total_transactions": 14,
            "category_breakdown": [
                {"category": "Food", "total": 1200.0},
                {"category": "Transport", "total": 600.0}
            ]
        }
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE date LIKE ?
        """, (f"{month}%",))
        total = (await cursor.fetchone())[0]

        await cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE date LIKE ?
            GROUP BY category
            ORDER BY total DESC
        """, (f"{month}%",))
        category_breakdown = [
            {"category": row[0], "total": row[1]}
            for row in await cursor.fetchall()
        ]

        await cursor.execute("""
            SELECT COUNT(*)
            FROM expenses
            WHERE date LIKE ?
        """, (f"{month}%",))
        total_transactions = (await cursor.fetchone())[0]

        return {
            "month": month,
            "total": total,
            "total_transactions": total_transactions,
            "category_breakdown": category_breakdown
        }


@mcp.resource('expense://recent')
async def get_recent_expenses():
    """
    MCP resource that returns the 10 most recently recorded expenses.

    Resource URI:
        expense://recent

    Fetches the latest expense entries ordered by date descending, capped at 10 records.
    Useful for a quick glance at recent spending activity without loading the full history.

    Returns:
        list[dict]: A list of up to 10 expense records, each containing:
            - id (int): The unique identifier of the expense.
            - date (str): The date of the expense in 'YYYY-MM-DD' format.
            - item_name (str): Name or description of the purchased item or service.
            - amount (float): The cost of the expense.
            - category (str): The expense category.
            - payment_method (str): The payment method used.
            - notes (str | None): Optional remarks; None if not provided.
          Ordered by date descending (most recent first).

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        # Accessing expense://recent returns:
        [
            {
                "id": 42, "date": "2024-06-18", "item_name": "Coffee",
                "amount": 80.0, "category": "Food", "payment_method": "UPI", "notes": None
            },
            ...
        ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT id, date, item_name, amount, category, payment_method, notes
            FROM expenses
            ORDER BY date DESC
            LIMIT 10
        """)

        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}

        return [
            {
                "id": row[0],
                "date": row[1],
                "item_name": row[2],
                "amount": row[3],
                "category": row[4],
                "payment_method": row[5],
                "notes": row[6]
            }
            for row in rows
        ]


@mcp.resource('expense://by-category/{category}')
async def get_expenses_by_category(category: str):
    """
    MCP resource that provides a full spending breakdown for a specific expense category.

    Resource URI:
        expense://by-category/{category}

    Returns the total amount spent, transaction count, and a detailed list of all
    individual expenses belonging to the given category, ordered most recent first.

    Args:
        category (str): The expense category to retrieve data for (e.g., 'Food', 'Transport').

    Returns:
        dict: A category report containing:
            - category (str): The queried category name.
            - total_spent (float): Cumulative amount spent in this category.
                                   Returns 0.0 if no records exist for it.
            - total_transactions (int): Number of expenses in this category.
            - transactions (list[dict]): Individual expense records, each containing:
                - id (int): The unique expense identifier.
                - date (str): Expense date in 'YYYY-MM-DD' format.
                - item_name (str): Name or description of the item or service.
                - amount (float): Cost of the expense.
                - payment_method (str): Payment method used.
                - notes (str | None): Optional remarks; None if not provided.
              Ordered by date descending. Empty list if no records exist.

    Example:
        # Accessing expense://by-category/Food returns:
        {
            "category": "Food",
            "total_spent": 4200.0,
            "total_transactions": 18,
            "transactions": [
                {
                    "id": 41, "date": "2024-06-17", "item_name": "Lunch",
                    "amount": 150.0, "payment_method": "Cash", "notes": None
                },
                ...
            ]
        }
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE category = ?
        """, (category,))
        total = (await cursor.fetchone())[0]

        await cursor.execute("""
            SELECT id, date, item_name, amount, payment_method, notes
            FROM expenses
            WHERE category = ?
            ORDER BY date DESC
        """, (category,))

        transactions = [
            {
                "id": row[0],
                "date": row[1],
                "item_name": row[2],
                "amount": row[3],
                "payment_method": row[4],
                "notes": row[5]
            }
            for row in await cursor.fetchall()
        ]

        return {
            "category": category,
            "total_spent": total,
            "total_transactions": len(transactions),
            "transactions": transactions
        }


@mcp.resource('expense://by-payment/{payment_method}')
async def get_expenses_by_payment(payment_method: str):
    """
    MCP resource that provides a full spending breakdown for a specific payment method.

    Resource URI:
        expense://by-payment/{payment_method}

    Returns the total amount spent, transaction count, and a detailed list of all
    individual expenses made via the given payment method, ordered most recent first.

    Args:
        payment_method (str): The payment method to retrieve data for
                              (e.g., 'Cash', 'Credit Card', 'UPI').

    Returns:
        dict: A payment method report containing:
            - payment_method (str): The queried payment method.
            - total_spent (float): Cumulative amount spent via this method.
                                   Returns 0.0 if no records exist for it.
            - total_transactions (int): Number of expenses using this payment method.
            - transactions (list[dict]): Individual expense records, each containing:
                - id (int): The unique expense identifier.
                - date (str): Expense date in 'YYYY-MM-DD' format.
                - item_name (str): Name or description of the item or service.
                - amount (float): Cost of the expense.
                - category (str): The expense category.
                - notes (str | None): Optional remarks; None if not provided.
              Ordered by date descending. Empty list if no records exist.

    Example:
        # Accessing expense://by-payment/UPI returns:
        {
            "payment_method": "UPI",
            "total_spent": 4200.0,
            "total_transactions": 20,
            "transactions": [
                {
                    "id": 38, "date": "2024-06-16", "item_name": "Grocery",
                    "amount": 250.0, "category": "Food", "notes": "Weekly shopping"
                },
                ...
            ]
        }
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE payment_method = ?
        """, (payment_method,))
        total = (await cursor.fetchone())[0]

        await cursor.execute("""
            SELECT id, date, item_name, amount, category, notes
            FROM expenses
            WHERE payment_method = ?
            ORDER BY date DESC
        """, (payment_method,))

        transactions = [
            {
                "id": row[0],
                "date": row[1],
                "item_name": row[2],
                "amount": row[3],
                "category": row[4],
                "notes": row[5]
            }
            for row in await cursor.fetchall()
        ]

        return {
            "payment_method": payment_method,
            "total_spent": total,
            "total_transactions": len(transactions),
            "transactions": transactions
        }


@mcp.resource('expense://payment-breakdown')
async def payment_method_breakdown():
    """
    MCP resource that returns a ranked spending breakdown across all payment methods.

    Resource URI:
        expense://payment-breakdown

    Groups all expense records by payment method and computes the transaction count
    and total spend for each, ordered by highest total spend first.

    Returns:
        list[dict]: A list of per-payment-method summaries, each containing:
            - payment_method (str): The payment method name.
            - total_transactions (int): Number of expenses recorded with this method.
            - total_spent (float): Cumulative amount spent via this method.
          Ordered by total_spent descending.

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        # Accessing expense://payment-breakdown returns:
        [
            {"payment_method": "Credit Card", "total_transactions": 12, "total_spent": 8750.0},
            {"payment_method": "UPI",         "total_transactions": 20, "total_spent": 4200.0},
            {"payment_method": "Cash",        "total_transactions": 5,  "total_spent": 900.0}
        ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT payment_method, COUNT(*) as transactions, COALESCE(SUM(amount), 0) as total
            FROM expenses
            GROUP BY payment_method
            ORDER BY total DESC
        """)

        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}

        return [
            {
                "payment_method": row[0],
                "total_transactions": row[1],
                "total_spent": row[2]
            }
            for row in rows
        ]

