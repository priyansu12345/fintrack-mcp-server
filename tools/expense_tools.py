from mcp_instance import mcp
from database import get_connection

ALLOWED_COLUMNS = {"date", "item_name", "amount", "category", "payment_method", "notes"}


@mcp.tool
async def add_expense(date: str, item_name: str, amount: float, category: str,
                payment_method: str, notes: str = None):
    """
    Add a new expense record to the database.

    Args:
        date (str): The date of the expense in 'YYYY-MM-DD' format (e.g., '2024-06-15').
        item_name (str): A short description or name of the purchased item or service.
        amount (float): The cost of the expense (e.g., 49.99).
        category (str): The category the expense belongs to (e.g., 'Food', 'Transport').
        payment_method (str): The method used to pay (e.g., 'Cash', 'Credit Card', 'UPI').
        notes (str, optional): Any additional remarks or context. Defaults to None.

    Returns:
        dict: A confirmation message indicating the expense was recorded successfully.

    Example:
        add_expense("2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping")
        # Returns: {"message": "Expense added successfully"}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            INSERT INTO expenses (date, item_name, amount, category, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, item_name, amount, category, payment_method, notes))
        await conn.commit()
        return {"message": "Expense added successfully"}


@mcp.tool
async def list_expenses():
    """
    Retrieve all expense records from the database.

    Returns:
        list[tuple]: A list of all expense rows, each containing
                     (id, date, item_name, amount, category, payment_method, notes).

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        list_expenses()
        # Returns: [
        #     (1, "2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping"),
        #     (2, "2024-06-16", "Bus Ticket", 30.0, "Transport", "Cash", None),
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('SELECT * FROM expenses')
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_expense(expense_id: int):
    """
    Retrieve a single expense record by its unique ID.

    Args:
        expense_id (int): The unique identifier of the expense to retrieve.

    Returns:
        list[tuple]: A list containing the matched expense row with fields
                     (id, date, item_name, amount, category, payment_method, notes).

        If no record is found for the given ID, returns:
            {"message": "No data found"}

    Example:
        get_expense(1)
        # Returns: [(1, "2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping")]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def update_expense(expense_id: int, to_update_column: str, to_update_value):
    """
    Update a specific field of an existing expense record.

    Only columns listed in ALLOWED_COLUMNS are permitted to be updated:
    {'date', 'item_name', 'amount', 'category', 'payment_method', 'notes'}.

    Args:
        expense_id (int): The unique identifier of the expense to update.
        to_update_column (str): The name of the column to update. Must be one
                                of the allowed columns listed above.
        to_update_value: The new value to set for the specified column.
                         The type should match the column's expected type
                         (str for text fields, float for amount).

    Returns:
        dict: A confirmation message indicating the update was applied.

    Raises:
        ValueError: If `to_update_column` is not in ALLOWED_COLUMNS.

    Example:
        update_expense(1, "amount", 300.0)
        # Returns: {"message": "Expense updated successfully"}

        update_expense(1, "invalid_col", "x")
        # Raises: ValueError: Invalid column: 'invalid_col'. Must be one of {...}
    """
    if to_update_column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column: '{to_update_column}'. Must be one of {ALLOWED_COLUMNS}")
    async with get_connection() as conn:
        cursor = await conn.cursor()
        query = f"UPDATE expenses SET {to_update_column} = ? WHERE id = ?"
        await cursor.execute(query, (to_update_value, expense_id))
        await conn.commit()
        return {"message": "Expense updated successfully"}


@mcp.tool
async def delete_expense(expense_id: int):
    """
    Permanently delete an expense record by its unique ID.

    Args:
        expense_id (int): The unique identifier of the expense to delete.

    Returns:
        dict: A confirmation message indicating which expense was deleted.

    Note:
        No error is raised if the given ID does not exist; the operation
        completes silently in that case.

    Example:
        delete_expense(3)
        # Returns: {"message": "Expense 3 deleted successfully"}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        await conn.commit()
        return {"message": f"Expense {expense_id} deleted successfully"}


@mcp.tool
async def get_expenses_by_category(category: str):
    """
    Retrieve all expense records belonging to a specific category.

    Args:
        category (str): The category name to filter by (e.g., 'Food', 'Transport').

    Returns:
        list[tuple]: A list of expense rows matching the given category, each containing
                     (id, date, item_name, amount, category, payment_method, notes).

        If no matching records are found, returns:
            {"message": "No data found"}

    Example:
        get_expenses_by_category("Food")
        # Returns: [
        #     (1, "2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping"),
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            WHERE category = ?
        ''', (category,))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_expenses_by_date(date: str):
    """
    Retrieve all expense records for a specific date.

    Args:
        date (str): The exact date to filter by in 'YYYY-MM-DD' format (e.g., '2024-06-15').

    Returns:
        list[tuple]: A list of expense rows recorded on the given date, each containing
                     (id, date, item_name, amount, category, payment_method, notes).

        If no records are found for that date, returns:
            {"message": "No data found"}

    Example:
        get_expenses_by_date("2024-06-15")
        # Returns: [
        #     (1, "2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping"),
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            WHERE date = ?
        ''', (date,))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_expenses_by_date_range(start_date: str, end_date: str):
    """
    Retrieve all expense records falling within a specified date range (inclusive).

    Args:
        start_date (str): The beginning of the date range in 'YYYY-MM-DD' format (e.g., '2024-06-01').
        end_date (str): The end of the date range in 'YYYY-MM-DD' format (e.g., '2024-06-30').

    Returns:
        list[tuple]: A list of expense rows with dates between start_date and end_date,
                     each containing (id, date, item_name, amount, category, payment_method, notes).

        If no records fall within the range, returns:
            {"message": "No data found"}

    Example:
        get_expenses_by_date_range("2024-06-01", "2024-06-30")
        # Returns: [
        #     (1, "2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping"),
        #     (2, "2024-06-16", "Bus Ticket", 30.0, "Transport", "Cash", None),
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            WHERE date >= ? AND date <= ?
        ''', (start_date, end_date))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_expenses_above_amount(amount: float):
    """
    Retrieve all expense records where the amount is greater than or equal to the given threshold.

    Args:
        amount (float): The minimum amount threshold to filter by (inclusive).

    Returns:
        list[tuple]: A list of expense rows with amount >= the given value, each containing
                     (id, date, item_name, amount, category, payment_method, notes).

        If no matching records are found, returns:
            {"message": "No data found"}

    Example:
        get_expenses_above_amount(500.0)
        # Returns all expenses where amount >= 500.0
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            WHERE amount >= ?
        ''', (amount,))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_expenses_below_amount(amount: float):
    """
    Retrieve all expense records where the amount is less than or equal to the given threshold.

    Args:
        amount (float): The maximum amount threshold to filter by (inclusive).

    Returns:
        list[tuple]: A list of expense rows with amount <= the given value, each containing
                    (id, date, item_name, amount, category, payment_method, notes).

        If no matching records are found, returns:
            {"message": "No data found"}

    Example:
        get_expenses_below_amount(100.0)
        # Returns all expenses where amount <= 100.0
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            WHERE amount <= ?
        ''', (amount,))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_total_expenses():
    """
    Calculate the total sum of all expense amounts across all records.

    Returns:
        tuple: A single-element tuple containing the sum of all expense amounts as a float
            (e.g., (4250.75,)).

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        get_total_expenses()
        # Returns: (4250.75,)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT SUM(amount)
            FROM expenses
        ''')
        rows = await cursor.fetchone()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_total_expenses_by_category(category: str):
    """
    Calculate the total amount spent in a specific expense category.

    Args:
        category (str): The category to sum expenses for (e.g., 'Food', 'Transport').

    Returns:
        tuple: A single-element tuple containing the total spent amount as a float
            (e.g., (1200.50,)). Returns (None,) if the category exists but has no amounts.

        If no records are found, returns:
            {"message": "No data found"}

    Example:
        get_total_expenses_by_category("Food")
        # Returns: (1200.50,)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT SUM(amount)
            FROM expenses
            WHERE category = ?
        ''', (category,))
        rows = await cursor.fetchone()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def expense_count():
    """
    Return the total number of expense records in the database.

    Returns:
        tuple: A single-element tuple containing the total count as an integer
            (e.g., (42,)).

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        expense_count()
        # Returns: (42,)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT COUNT(*)
            FROM expenses
        ''')
        rows = await cursor.fetchone()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def average_expense():
    """
    Calculate the average amount across all expense records.

    Returns:
        tuple: A single-element tuple containing the average expense amount as a float,
            rounded to SQLite's default precision (e.g., (185.50,)).

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        average_expense()
        # Returns: (185.50,)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT AVG(amount)
            FROM expenses
        ''')
        rows = await cursor.fetchone()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def top_expense(limit):
    """
    Retrieve the single highest expense record from the top N expenses, ordered by amount.

    Args:
        limit (int): The number of top expenses to consider before returning the first one.
                For example, limit=5 fetches the top 5 by amount and returns only the first.

    Returns:
        tuple: The expense row with the highest amount among the top `limit` records, containing
            (id, date, item_name, amount, category, payment_method, notes).

        If no records exist, returns:
            {"message": "No data found"}

    Note:
        This tool uses fetchone(), so it always returns at most one row regardless of `limit`.
        To retrieve all top N expenses, use a different query with fetchall().

    Example:
        top_expense(5)
        # Returns: (7, "2024-06-20", "Laptop", 55000.0, "Electronics", "Credit Card", None)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            ORDER BY amount DESC
            LIMIT ?
        ''', (limit,))
        rows = await cursor.fetchone()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def category_breakdown():
    """
    Retrieve the total amount spent per expense category.

    Returns:
        tuple: A single row containing (category, total_amount) for the first category
            returned by the GROUP BY query.

        If no records exist, returns:
            {"message": "No data found"}

    Note:
        This tool uses fetchone(), so it returns only one category row despite the GROUP BY.
        To retrieve a breakdown for all categories, use fetchall() instead.

    Example:
        category_breakdown()
        # Returns: ("Food", 1200.50)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT category, SUM(amount)
            FROM expenses
            GROUP BY category
        ''')
        rows = await cursor.fetchone()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def highest_spending_category():
    """
    Identify the expense category with the highest total spending.

    Returns:
        tuple: A single row containing (category, total_amount) for the category
            with the greatest cumulative spend (e.g., ("Food", 3200.0)).

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        highest_spending_category()
        # Returns: ("Food", 3200.0)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT category, SUM(amount) AS total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        ''')
        row = await cursor.fetchone()
        if not row:
            return {"message": "No data found"}
        return row


@mcp.tool
async def get_expenses_by_payment_method(payment_method: str):
    """
    Retrieve all expense records that used a specific payment method.

    Args:
        payment_method (str): The payment method to filter by (e.g., 'Cash', 'Credit Card', 'UPI').

    Returns:
        list[tuple]: A list of expense rows paid via the given method, each containing
                    (id, date, item_name, amount, category, payment_method, notes).

        If no matching records are found, returns:
            {"message": "No data found"}

    Example:
        get_expenses_by_payment_method("UPI")
        # Returns: [
        #     (1, "2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping"),
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            WHERE payment_method = ?
        ''', (payment_method,))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows


@mcp.tool
async def get_total_by_payment_method(payment_method: str):
    """
    Calculate the total amount spent using a specific payment method.

    Args:
        payment_method (str): The payment method to sum expenses for
        (e.g., 'Cash', 'Credit Card', 'UPI').

    Returns:
        dict: A summary containing:
            - payment_method (str): The queried payment method.
            - total_spent (float): The total amount spent via this method.
            Returns 0.0 if no expenses exist for it.

    Example:
        get_total_by_payment_method("Credit Card")
        # Returns: {"payment_method": "Credit Card", "total_spent": 8750.0}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE payment_method = ?
        ''', (payment_method,))
        total = (await cursor.fetchone())[0]
        return {
            "payment_method": payment_method,
            "total_spent": total
        }


@mcp.tool
async def payment_method_breakdown():
    """
    Return a ranked breakdown of spending and transaction count per payment method.

    Results are ordered by total amount spent in descending order.

    Returns:
        list[dict]: A list of summaries per payment method, each containing:
            - payment_method (str): The payment method name.
            - total_transactions (int): Number of expenses recorded with this method.
            - total_spent (float): Cumulative amount spent via this method.

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        payment_method_breakdown()
        # Returns: [
        #     {"payment_method": "Credit Card", "total_transactions": 12, "total_spent": 8750.0},
        #     {"payment_method": "UPI", "total_transactions": 20, "total_spent": 4200.0},
        #     {"payment_method": "Cash", "total_transactions": 5, "total_spent": 900.0},
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT payment_method, COUNT(*) as transactions, SUM(amount) as total
            FROM expenses
            GROUP BY payment_method
            ORDER BY total DESC
        ''')
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


@mcp.tool
async def most_used_payment_method():
    """
    Identify the payment method used most frequently across all expense records.

    Returns:
        dict: A summary of the most-used payment method containing:
            - payment_method (str): The name of the most frequently used payment method.
            - total_transactions (int): The number of times this method was used.

        If no records exist, returns:
            {"message": "No data found"}

    Example:
        most_used_payment_method()
        # Returns: {"payment_method": "UPI", "total_transactions": 20}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT payment_method, COUNT(*) as transactions
            FROM expenses
            GROUP BY payment_method
            ORDER BY transactions DESC
            LIMIT 1
        ''')
        row = await cursor.fetchone()
        if not row:
            return {"message": "No data found"}
        return {
            "payment_method": row[0],
            "total_transactions": row[1]
        }


@mcp.tool
async def get_expenses_by_category_and_payment_method(category: str, payment_method: str):
    """
    Retrieve all expense records matching both a specific category and payment method.

    Args:
        category (str): The expense category to filter by (e.g., 'Food', 'Transport').
        payment_method (str): The payment method to filter by (e.g., 'Cash', 'UPI').

    Returns:
        list[tuple]: A list of expense rows matching both filters, each containing
                     (id, date, item_name, amount, category, payment_method, notes).

        If no records match both criteria, returns:
            {"message": "No data found"}

    Example:
        get_expenses_by_category_and_payment_method("Food", "UPI")
        # Returns: [
        #     (1, "2024-06-15", "Grocery", 250.0, "Food", "UPI", "Weekly shopping"),
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            SELECT *
            FROM expenses
            WHERE category = ? AND payment_method = ?
        ''', (category, payment_method))
        rows = await cursor.fetchall()
        if not rows:
            return {"message": "No data found"}
        return rows

@mcp.tool
async def highest_spending_category_by_month(month:str):
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """SELECT source, SUM(amount) as total
               FROM incomes
               GROUP BY source
               ORDER BY total DESC
               LIMIT 1"""
        )
        row = await cursor.fetchone()

    if row is None:
        return {"error": "No income records found"}

    return {
        "source": row[0],
        "total_income": row[1]
    }


