from mcp_instance import mcp
from database import get_connection


@mcp.tool
async def add_income(date: str, source: str, amount: float, notes: str = None):
    """
    Add a new income record to the database.

    Args:
        date (str): The date of the income in 'YYYY-MM-DD' format.
        source (str): The source of the income (e.g., 'Salary', 'Freelance').
        amount (float): The income amount.
        notes (str, optional): Any additional notes about the income. Defaults to None.

    Returns:
        dict: A success message confirming the income was added.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "INSERT INTO incomes (date, source, amount, notes) VALUES (?, ?, ?, ?)",
            (date, source, amount, notes)
        )
        await conn.commit()
    return {"message": "Income added successfully"}


@mcp.tool
async def get_incomes():
    """
    Retrieve all income records from the database.

    Returns:
        list[dict]: A list of all income records, each containing
                    id, date, source, amount, and notes.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM incomes")
        rows = await cursor.fetchall()
    return [
        {"id": row[0], "date": row[1], "source": row[2], "amount": row[3], "notes": row[4]}
        for row in rows
    ]


@mcp.tool
async def get_income(income_id: int):
    """
    Retrieve a single income record by its ID.

    Args:
        income_id (int): The unique identifier of the income record.

    Returns:
        dict | None: The income record as a dict if found, otherwise None.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM incomes WHERE id = ?", (income_id,))
        row = await cursor.fetchone()
    if row is None:
        return None
    return {"id": row[0], "date": row[1], "source": row[2], "amount": row[3], "notes": row[4]}


@mcp.tool
async def update_income(income_id: int, source: str, amount: float, date: str, notes: str = None):
    """
    Update an existing income record by its ID.

    Args:
        income_id (int): The unique identifier of the income record to update.
        source (str): The updated income source.
        amount (float): The updated income amount.
        date (str): The updated date in 'YYYY-MM-DD' format.
        notes (str, optional): Updated notes for the income record. Defaults to None.

    Returns:
        dict: A success message confirming the update, or an error message if not found.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """UPDATE incomes
               SET source = ?, amount = ?, date = ?, notes = ?
               WHERE id = ?""",
            (source, amount, date, notes, income_id)
        )
        await conn.commit()
        if cursor.rowcount == 0:
            return {"error": f"No income record found with id {income_id}"}
    return {"message": "Income updated successfully"}


@mcp.tool
async def delete_income(income_id: int):
    """
    Delete an income record from the database by its ID.

    Args:
        income_id (int): The unique identifier of the income record to delete.

    Returns:
        dict: A success message if deleted, or an error message if no record was found.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM incomes WHERE id = ?", (income_id,))
        await conn.commit()
        if cursor.rowcount == 0:
            return {"error": f"No income record found with id {income_id}"}
    return {"message": f"Income with id {income_id} deleted successfully"}


@mcp.tool
async def get_total_income():
    """
    Calculate the total sum of all income records.

    Returns:
        dict: A dict containing the total income amount.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes")
        row = await cursor.fetchone()
    return {"total_income": row[0]}


@mcp.tool
async def get_income_by_source(source: str):
    """
    Retrieve all income records matching a specific source.

    Args:
        source (str): The income source to filter by (e.g., 'Salary', 'Freelance').

    Returns:
        list[dict]: A list of income records matching the given source.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM incomes WHERE source = ?", (source,))  
        rows = await cursor.fetchall() 
    return [
        {"id": row[0], "date": row[1], "source": row[2], "amount": row[3], "notes": row[4]}
        for row in rows
    ]


@mcp.tool
async def get_income_by_date_range(start_date: str, end_date: str):
    """
    Retrieve all income records within a specified date range.

    Args:
        start_date (str): The start date in 'YYYY-MM-DD' format (inclusive).
        end_date (str): The end date in 'YYYY-MM-DD' format (inclusive).

    Returns:
        list[dict]: A list of income records within the given date range.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM incomes WHERE date >= ? AND date <= ?",
            (start_date, end_date)
        )
        rows = await cursor.fetchall() 
    return [
        {"id": row[0], "date": row[1], "source": row[2], "amount": row[3], "notes": row[4]}
        for row in rows
    ]


@mcp.tool
async def get_monthly_savings(month: str):
    """
    Calculate the total savings for a specific month (income - expenses).

    Args:
        month (str): The month to calculate savings for in 'YYYY-MM' format (e.g., '2025-06').

    Returns:
        dict: A dict containing the month, total income, total expenses, and net savings.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM incomes WHERE strftime('%Y-%m', date) = ?",
            (month,)
        )
        total_income = (await cursor.fetchone())[0]

        await cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE strftime('%Y-%m', date) = ?",
            (month,)
        )
        total_expenses = (await cursor.fetchone())[0]

    return {
        "month": month,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": total_income - total_expenses
    }


@mcp.tool
async def saving_rate(month: str):
    """
    Calculate the savings rate as a percentage of income for a specific month.

    Args:
        month (str): The month to calculate the savings rate for in 'YYYY-MM' format (e.g., '2025-06').

    Returns:
        dict: A dict containing the month, net savings, total income, and savings rate percentage.
            Returns an error message if total income is zero to avoid division by zero.
    """
    report = await get_monthly_savings(month)

    if report["total_income"] == 0:  
        return {"error": f"No income recorded for month {month}, savings rate cannot be calculated"}

    return {
        "month": month,
        "total_income": report["total_income"],
        "net_savings": report["net_savings"],
        "savings_rate": round((report["net_savings"] / report["total_income"]) * 100, 2)
    }

@mcp.tool
async def financial_summary(month: str):
    """
    Generate a complete financial summary for a specific month.

    Args:
        month (str): The month to summarize in 'YYYY-MM' format (e.g., '2025-06').

    Returns:
        dict: A dict containing total income, total expenses, net savings, and savings rate.
            Returns an error message if total income is zero.
    """
    report1 = await get_monthly_savings(month)     
    report2 = await saving_rate(month)

    if "error" in report2:                
        return {
            "month": month,
            "total_income": report1["total_income"],
            "total_expenses": report1["total_expenses"],
            "net_savings": report1["net_savings"],
            "savings_rate": "N/A (no income recorded this month)"
        }

    return {
        "month": month,
        "total_income": report1["total_income"],
        "total_expenses": report1["total_expenses"],
        "net_savings": report1["net_savings"],
        "savings_rate": report2["savings_rate"]
    }

@mcp.tool
async def highest_income_source():
    """
    Find the income source that has generated the most total income.

    Returns:
        dict: A dict containing the top income source and its total amount.
              Returns an error message if no income records exist.
    """
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




