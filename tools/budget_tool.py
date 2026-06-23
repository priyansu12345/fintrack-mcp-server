from mcp_instance import mcp
from database import get_connection
import asyncpg


@mcp.tool
async def set_budget(category: str, month: str, monthly_limit: float):
    """
    Create a new budget entry for a specific category and month.

    Args:
        category (str): The expense category to budget for (e.g., 'Food', 'Transport').
        month (str): The month for the budget in 'YYYY-MM' format (e.g., '2024-06').
        monthly_limit (float): The maximum spending limit for the category in the given month.

    Returns:
        dict: A confirmation message indicating the budget was added successfully.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}
    if monthly_limit <= 0:
        return {"error": "Monthly limit must be greater than 0"}

    try:
        async with get_connection() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM budgets WHERE category = $1 AND month = $2",
                category, month
            )
            if existing:
                return {"error": f"Budget for '{category}' in {month} already exists. Use update_budget to modify it."}

            await conn.execute(
                '''INSERT INTO budgets(category, month, monthly_limit)
                VALUES ($1, $2, $3)''',
                category, month, monthly_limit
            )
            return {"message": "Budget added successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_budget(category: str, month: str):
    """
    Retrieve the budget record for a specific category and month.

    Args:
        category (str): The expense category to look up.
        month (str): The month to look up in 'YYYY-MM' format.

    Returns:
        dict | None: Budget record or None if not found.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}

    try:
        async with get_connection() as conn:
            row = await conn.fetchrow(
                '''SELECT * FROM budgets
                WHERE category = $1 AND month = $2''',
                category, month
            )
            if not row:
                return {"message": f"No budget found for '{category}' in {month}"}
            return dict(row)
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def list_budgets():
    """
    Retrieve all budget records sorted alphabetically by category.

    Returns:
        list[dict]: A list of all budget rows ordered by category.
    """
    try:
        async with get_connection() as conn:
            rows = await conn.fetch(
                '''SELECT * FROM budgets ORDER BY category'''
            )
            if not rows:
                return {"message": "No budgets have been configured yet."}
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_budget_status(category: str, month: str):
    """
    Get a detailed spending status report for a specific category and month.

    Returns:
        dict: Status report with budget, spent, remaining, percentage_used.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}

    try:
        async with get_connection() as conn:
            budget_row = await conn.fetchrow("""
                SELECT monthly_limit FROM budgets
                WHERE category = $1 AND month = $2
            """, category, month)

            if not budget_row:
                return {"message": f"No budget found for '{category}' in {month}"}

            budget = budget_row["monthly_limit"]

            if budget <= 0:
                return {"error": f"Invalid budget limit ({budget}) for '{category}' in {month}"}

            spent_row = await conn.fetchrow("""
                SELECT SUM(amount) as total FROM expenses
                WHERE category = $1 AND date LIKE $2
            """, category, f"{month}%")

            spent = spent_row["total"] or 0
            remaining = budget - spent
            percentage_used = round((spent / budget) * 100, 2)

            return {
                "category": category,
                "month": month,
                "budget": budget,
                "spent": spent,
                "remaining": remaining,
                "percentage_used": percentage_used
            }
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def check_budget_alerts():
    """
    Check all budgets and return alert status for each.

    Returns:
        list[dict]: Alert reports with status: HEALTHY, WARNING, or OVER_BUDGET.
    """
    try:
        async with get_connection() as conn:
            all_budgets = await conn.fetch("""
                SELECT category, month, monthly_limit FROM budgets
            """)

            if not all_budgets:
                return {"message": "No budgets have been configured yet."}

            results = []

            for row in all_budgets:
                category = row["category"]
                month = row["month"]
                monthly_limit = row["monthly_limit"]

                if monthly_limit <= 0:
                    results.append({
                        "category": category,
                        "month": month,
                        "error": f"Invalid monthly limit ({monthly_limit}) — skipping"
                    })
                    continue

                spent_row = await conn.fetchrow("""
                    SELECT COALESCE(SUM(amount), 0) as total FROM expenses
                    WHERE category = $1 AND date LIKE $2
                """, category, f"{month}%")

                spent = spent_row["total"]
                remaining = monthly_limit - spent
                percentage_used = round((spent / monthly_limit) * 100, 2)

                if percentage_used >= 100:
                    status = "OVER_BUDGET"
                elif percentage_used >= 80:
                    status = "WARNING"
                else:
                    status = "HEALTHY"

                results.append({
                    "category": category,
                    "month": month,
                    "monthly_limit": monthly_limit,
                    "spent": spent,
                    "remaining": remaining,
                    "percentage_used": percentage_used,
                    "status": status
                })

            return results
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def delete_budget(category: str, month: str):
    """
    Delete the budget record for a specific category and month.

    Returns:
        dict: Confirmation message.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}

    try:
        async with get_connection() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM budgets WHERE category = $1 AND month = $2",
                category, month
            )
            if not existing:
                return {"message": f"No budget found for '{category}' in {month}. Nothing to delete."}

            await conn.execute(
                '''DELETE FROM budgets WHERE category = $1 AND month = $2''',
                category, month
            )
        return {"message": f"Budget for {category} ({month}) deleted successfully"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def update_budget(category: str, month: str, new_limit: float):
    """
    Update the monthly spending limit for an existing budget.

    Returns:
        dict: Confirmation message or not-found message.
    """
    if not category or not category.strip():
        return {"error": "Category cannot be empty"}
    if not month or not month.strip():
        return {"error": "Month cannot be empty"}
    if new_limit <= 0:
        return {"error": "New limit must be greater than 0"}

    try:
        async with get_connection() as conn:
            result = await conn.execute("""
                UPDATE budgets SET monthly_limit = $1
                WHERE category = $2 AND month = $3
            """, new_limit, category, month)

            rows_affected = int(result.split()[-1])

            if rows_affected == 0:
                return {"message": f"Budget not found for '{category}' in {month}"}

            return {"message": f"{category}'s {month} budget updated to {new_limit}"}
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def list_over_budget_details():
    """
    Retrieve detailed information for all over-budget categories.

    Returns:
        list[dict]: Over-budget entries with exceeded_by and percentage_used.
    """
    try:
        async with get_connection() as conn:
            all_budgets = await conn.fetch("""
                SELECT category, month, monthly_limit FROM budgets
            """)

            if not all_budgets:
                return {"message": "No budgets have been configured yet."}

            over_budget = []

            for row in all_budgets:
                category = row["category"]
                month = row["month"]
                monthly_limit = row["monthly_limit"]

                if monthly_limit <= 0:
                    continue

                spent_row = await conn.fetchrow("""
                    SELECT COALESCE(SUM(amount), 0) as total FROM expenses
                    WHERE category = $1 AND date LIKE $2
                """, category, f"{month}%")

                spent = spent_row["total"]
                percentage_used = round((spent / monthly_limit) * 100, 2)

                if percentage_used >= 100:
                    over_budget.append({
                        "category": category,
                        "month": month,
                        "monthly_limit": monthly_limit,
                        "spent": spent,
                        "exceeded_by": round(spent - monthly_limit, 2),
                        "percentage_used": percentage_used
                    })

            if not over_budget:
                return {"message": "All categories are within budget!"}

            return over_budget
    except asyncpg.PostgresError as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def budget_health_report():
    """
    Generate a high-level summary report of budget health across all categories.

    Returns:
        dict: Counts of HEALTHY, WARNING, OVER_BUDGET, TOTAL_BUDGETS.
    """
    try:
        reports = await check_budget_alerts()

        if isinstance(reports, dict):
            return reports

        response = {
            "HEALTHY": 0,
            "WARNING": 0,
            "OVER_BUDGET": 0,
            "TOTAL_BUDGETS": 0
        }

        for report in reports:
            if "error" in report:
                continue
            status = report.get("status")
            if status == "HEALTHY":
                response["HEALTHY"] += 1
            elif status == "WARNING":
                response["WARNING"] += 1
            elif status == "OVER_BUDGET":
                response["OVER_BUDGET"] += 1

        response["TOTAL_BUDGETS"] = len(reports)
        return response
    except Exception as e:
        return {"error": f"Unexpected error generating health report: {str(e)}"}
