from mcp_instance import mcp
from database import get_connection


@mcp.tool
async def add_income(date: str, source: str, amount: float, notes: str = None):
    """
    Add a new income record to the database.
    """
    async with get_connection() as conn:
        await conn.execute(
            "INSERT INTO incomes (date, source, amount, notes) VALUES ($1, $2, $3, $4)",
            date, source, amount, notes
        )
    return {"message": "Income added successfully"}


@mcp.tool
async def get_incomes():
    """
    Retrieve all income records from the database.
    """
    async with get_connection() as conn:
        rows = await conn.fetch("SELECT * FROM incomes")
    return [dict(row) for row in rows]


@mcp.tool
async def get_income(income_id: int):
    """
    Retrieve a single income record by its ID.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM incomes WHERE id = $1", income_id)
    if row is None:
        return None
    return dict(row)


@mcp.tool
async def update_income(income_id: int, source: str, amount: float, date: str, notes: str = None):
    """
    Update an existing income record by its ID.
    """
    async with get_connection() as conn:
        result = await conn.execute(
            """UPDATE incomes
               SET source = $1, amount = $2, date = $3, notes = $4
               WHERE id = $5""",
            source, amount, date, notes, income_id
        )
        rows_affected = int(result.split()[-1])
        if rows_affected == 0:
            return {"error": f"No income record found with id {income_id}"}
    return {"message": "Income updated successfully"}


@mcp.tool
async def delete_income(income_id: int):
    """
    Delete an income record from the database by its ID.
    """
    async with get_connection() as conn:
        result = await conn.execute("DELETE FROM incomes WHERE id = $1", income_id)
        rows_affected = int(result.split()[-1])
        if rows_affected == 0:
            return {"error": f"No income record found with id {income_id}"}
    return {"message": f"Income with id {income_id} deleted successfully"}


@mcp.tool
async def get_total_income():
    """
    Calculate the total sum of all income records.
    """
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT COALESCE(SUM(amount), 0) as total FROM incomes")
    return {"total_income": row["total"]}


@mcp.tool
async def get_income_by_source(source: str):
    """
    Retrieve all income records matching a specific source.
    """
    async with get_connection() as conn:
        rows = await conn.fetch("SELECT * FROM incomes WHERE source = $1", source)
    return [dict(row) for row in rows]


@mcp.tool
async def get_income_by_date_range(start_date: str, end_date: str):
    """
    Retrieve all income records within a specified date range.
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM incomes WHERE date >= $1 AND date <= $2",
            start_date, end_date
        )
    return [dict(row) for row in rows]


@mcp.tool
async def get_monthly_savings(month: str):
    """
    Calculate the total savings for a specific month (income - expenses).
    """
    async with get_connection() as conn:
        income_row = await conn.fetchrow(
            "SELECT COALESCE(SUM(amount), 0) as total FROM incomes WHERE TO_CHAR(date::date, 'YYYY-MM') = $1",
            month
        )
        expense_row = await conn.fetchrow(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE TO_CHAR(date::date, 'YYYY-MM') = $1",
            month
        )

    total_income = income_row["total"]
    total_expenses = expense_row["total"]

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
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """SELECT source, SUM(amount) as total
               FROM incomes
               GROUP BY source
               ORDER BY total DESC
               LIMIT 1"""
        )

    if row is None:
        return {"error": "No income records found"}

    return {
        "source": row["source"],
        "total_income": row["total"]
    }
