from mcp_instance import mcp
from database import get_connection
import asyncpg
from datetime import datetime


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
async def add_income(date: str, source: str, amount: float, notes: str = None):
    """
    Add a new income record to the database.
    """
    if not date or not date.strip():
        return {"error": "Date cannot be empty"}
    if not _validate_date(date):
        return {"error": f"Invalid date format '{date}'. Expected YYYY-MM-DD"}
    if not source or not source.strip():
        return {"error": "Source cannot be empty"}
    if amount <= 0:
        return {"error": "Amount must be greater than 0"}

    try:
        async with get_connection() as conn:
            await conn.execute(
                "INSERT INTO incomes (date, source, amount, notes) VALUES ($1, $2, $3, $4)",
                date, source, amount, notes
            )
        return {"message": "Income added successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_incomes():
    """
    Retrieve all income records from the database.
    """
    try:
        async with get_connection() as conn:
            rows = await conn.fetch("SELECT * FROM incomes")
        if not rows:
            return {"message": "No income records found"}
        return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_income(income_id: int):
    """
    Retrieve a single income record by its ID.
    """
    if income_id <= 0:
        return {"error": "Income ID must be a positive integer"}

    try:
        async with get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM incomes WHERE id = $1", income_id)
        if row is None:
            return {"error": f"No income record found with ID {income_id}"}
        return dict(row)
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def update_income(income_id: int, source: str, amount: float, date: str, notes: str = None):
    """
    Update an existing income record by its ID.
    """
    if income_id <= 0:
        return {"error": "Income ID must be a positive integer"}
    if not date or not date.strip():
        return {"error": "Date cannot be empty"}
    if not _validate_date(date):
        return {"error": f"Invalid date format '{date}'. Expected YYYY-MM-DD"}
    if not source or not source.strip():
        return {"error": "Source cannot be empty"}
    if amount <= 0:
        return {"error": "Amount must be greater than 0"}

    try:
        async with get_connection() as conn:
            result = await conn.execute(
                """UPDATE incomes
                   SET source = $1, amount = $2, date = $3, notes = $4
                   WHERE id = $5""",
                source, amount, date, notes, income_id
            )
            rows_affected = int(result.split()[-1])
            if rows_affected == 0:
                return {"error": f"No income record found with ID {income_id}"}
        return {"message": "Income updated successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def delete_income(income_id: int):
    """
    Delete an income record from the database by its ID.
    """
    if income_id <= 0:
        return {"error": "Income ID must be a positive integer"}

    try:
        async with get_connection() as conn:
            result = await conn.execute("DELETE FROM incomes WHERE id = $1", income_id)
            rows_affected = int(result.split()[-1])
            if rows_affected == 0:
                return {"error": f"No income record found with ID {income_id}"}
        return {"message": f"Income with ID {income_id} deleted successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_total_income():
    """
    Calculate the total sum of all income records.
    """
    try:
        async with get_connection() as conn:
            row = await conn.fetchrow("SELECT COALESCE(SUM(amount), 0) as total FROM incomes")
        if row is None:
            return {"error": "Failed to retrieve total income"}
        return {"total_income": row["total"]}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_income_by_source(source: str):
    """
    Retrieve all income records matching a specific source.
    """
    if not source or not source.strip():
        return {"error": "Source cannot be empty"}

    try:
        async with get_connection() as conn:
            rows = await conn.fetch("SELECT * FROM incomes WHERE source = $1", source)
        if not rows:
            return {"message": f"No income records found for source '{source}'"}
        return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_income_by_date_range(start_date: str, end_date: str):
    """
    Retrieve all income records within a specified date range.
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
            rows = await conn.fetch(
                "SELECT * FROM incomes WHERE date >= $1 AND date <= $2",
                start_date, end_date
            )
        if not rows:
            return {"message": f"No income records found between '{start_date}' and '{end_date}'"}
        return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_monthly_savings(month: str):
    """
    Calculate the total savings for a specific month (income - expenses).
    """
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}
    if not _validate_month(month):
        return {"error": f"Invalid month format '{month}'. Expected YYYY-MM"}

    try:
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
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def saving_rate(month: str):
    """
    Calculate the savings rate as a percentage of income for a specific month.
    """
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}
    if not _validate_month(month):
        return {"error": f"Invalid month format '{month}'. Expected YYYY-MM"}

    report = await get_monthly_savings(month)

    if "error" in report:
        return report

    if report["total_income"] == 0:
        return {"error": f"No income recorded for month '{month}', savings rate cannot be calculated"}

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
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}
    if not _validate_month(month):
        return {"error": f"Invalid month format '{month}'. Expected YYYY-MM"}

    report1 = await get_monthly_savings(month)

    if "error" in report1:
        return report1

    report2 = await saving_rate(month)

    return {
        "month": month,
        "total_income": report1["total_income"],
        "total_expenses": report1["total_expenses"],
        "net_savings": report1["net_savings"],
        "savings_rate": report2.get("savings_rate", "N/A (no income recorded this month)")
    }


@mcp.tool
async def highest_income_source():
    """
    Find the income source that has generated the most total income.
    """
    try:
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
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
