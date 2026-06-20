from mcp_instance import mcp
from database import get_connection


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

    Example:
        set_budget("Food", "2024-06", 500.0)
        # Returns: {"message": "Budget added successfully"}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            '''INSERT INTO budgets(category, month, monthly_limit)
            VALUES (?, ?, ?)''',
            (category, month, monthly_limit)
        )
        await conn.commit()
        return {"message": "Budget added successfully"}


@mcp.tool
async def get_budget(category: str, month: str):
    """
    Retrieve the budget record for a specific category and month.

    Args:
        category (str): The expense category to look up (e.g., 'Food', 'Transport').
        month (str): The month to look up in 'YYYY-MM' format (e.g., '2024-06').

    Returns:
        tuple | None: A single row from the budgets table containing
                    (category, month, monthly_limit), or None if no record is found.

    Example:
        get_budget("Food", "2024-06")
        # Returns: ("Food", "2024-06", 500.0)
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            '''SELECT *
            FROM budgets
            WHERE category = ? AND month = ?''',
            (category, month)
        )
        rows = await cursor.fetchone()
        return rows


@mcp.tool
async def list_budgets():
    """
    Retrieve all budget records sorted alphabetically by category.

    Returns:
        list[tuple]: A list of all budget rows, each containing
                     (category, month, monthly_limit), ordered by category.
                     Returns an empty list if no budgets have been set.

    Example:
        list_budgets()
        # Returns: [("Food", "2024-06", 500.0), ("Transport", "2024-06", 200.0), ...]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            '''SELECT *
               FROM budgets
               ORDER BY category'''
        )
        rows = await cursor.fetchall()
        return rows


@mcp.tool
async def get_budget_status(category: str, month: str):
    """
    Get a detailed spending status report for a specific category and month.

    Compares the configured budget limit against actual expenses recorded
    for the given category and month, and computes remaining balance and
    percentage of budget used.

    Args:
        category (str): The expense category to check (e.g., 'Food', 'Transport').
        month (str): The month to check in 'YYYY-MM' format (e.g., '2024-06').

    Returns:
        dict: A status report containing:
            - category (str): The expense category.
            - month (str): The queried month.
            - budget (float): The configured monthly spending limit.
            - spent (float): Total amount spent in this category for the month.
            - remaining (float): Remaining budget (budget - spent); can be negative if over budget.
            - percentage_used (float): Percentage of the budget consumed, rounded to 2 decimal places.

        If no budget is found for the given category and month, returns:
            {"message": "Budget not found"}

    Example:
        get_budget_status("Food", "2024-06")
        # Returns: {
        #     "category": "Food",
        #     "month": "2024-06",
        #     "budget": 500.0,
        #     "spent": 320.0,
        #     "remaining": 180.0,
        #     "percentage_used": 64.0
        # }
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT monthly_limit
            FROM budgets
            WHERE category = ?
            AND month = ?
        """, (category, month))

        budget_row = await cursor.fetchone()

        if not budget_row:
            return {"message": "Budget not found"}

        budget = budget_row[0]

        await cursor.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE category = ?
            AND date LIKE ?
        """, (category, f"{month}%"))

        spent_row = await cursor.fetchone()
        spent = spent_row[0] or 0
        remaining = budget - spent
        percentage_used = round((spent / budget) * 100, 2) if budget > 0 else 0

        return {
            "category": category,
            "month": month,
            "budget": budget,
            "spent": spent,
            "remaining": remaining,
            "percentage_used": percentage_used
        }


@mcp.tool
async def check_budget_alerts():
    """
    Check all budgets and return an alert status for each based on spending thresholds.

    Evaluates every configured budget against actual expenses and assigns a
    status based on the percentage of the budget consumed:
        - 'HEALTHY'     : Less than 80% of the budget has been spent.
        - 'WARNING'     : Between 80% and 99% of the budget has been spent.
        - 'OVER_BUDGET' : 100% or more of the budget has been spent.

    Returns:
        list[dict]: A list of alert reports, one per budget, each containing:
            - category (str): The expense category.
            - month (str): The budget month.
            - monthly_limit (float): The configured spending limit.
            - spent (float): Total amount spent for the category and month.
            - remaining (float): Remaining balance (can be negative if over budget).
            - percentage_used (float): Budget consumption percentage, rounded to 2 decimal places.
            - status (str): One of 'HEALTHY', 'WARNING', or 'OVER_BUDGET'.

        If no budgets are configured, returns:
            {"message": "No budgets have been configured yet."}

    Example:
        check_budget_alerts()
        # Returns: [
        #     {"category": "Food", "month": "2024-06", "monthly_limit": 500.0,
        #      "spent": 420.0, "remaining": 80.0, "percentage_used": 84.0, "status": "WARNING"},
        #     {"category": "Transport", "month": "2024-06", "monthly_limit": 200.0,
        #      "spent": 90.0, "remaining": 110.0, "percentage_used": 45.0, "status": "HEALTHY"},
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT category, month, monthly_limit
            FROM budgets
        """)

        all_budgets = await cursor.fetchall()

        if not all_budgets:
            return {"message": "No budgets have been configured yet."}

        results = []

        for category, month, monthly_limit in all_budgets:
            await cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE category = ?
                AND date LIKE ?
            """, (category, f"{month}%"))

            spent = (await cursor.fetchone())[0]
            remaining = monthly_limit - spent
            percentage_used = round((spent / monthly_limit) * 100, 2) if monthly_limit > 0 else 0

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


@mcp.tool
async def delete_budget(category: str, month: str):
    """
    Delete the budget record for a specific category and month.

    Args:
        category (str): The expense category whose budget should be deleted (e.g., 'Food').
        month (str): The month of the budget to delete in 'YYYY-MM' format (e.g., '2024-06').

    Returns:
        dict: A confirmation message indicating the budget was deleted.

    Note:
        No error is raised if the specified budget does not exist; the operation
        completes silently in that case.

    Example:
        delete_budget("Food", "2024-06")
        # Returns: {"message": "Budget for Food (2024-06) deleted successfully"}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            '''DELETE FROM budgets
               WHERE category = ? AND month = ?''',
            (category, month)
        )
        await conn.commit()
    return {"message": f"Budget for {category} ({month}) deleted successfully"}


@mcp.tool
async def update_budget(category: str, month: str, new_limit: float):
    """
    Update the monthly spending limit for an existing budget.

    Args:
        category (str): The expense category whose budget should be updated (e.g., 'Food').
        month (str): The month of the budget to update in 'YYYY-MM' format (e.g., '2024-06').
        new_limit (float): The new monthly spending limit to set.

    Returns:
        dict: A confirmation message with the updated limit if the record was found, or
              a not-found message if no matching budget exists.

    Example:
        update_budget("Food", "2024-06", 600.0)
        # Returns: {"message": "Food's 2024-06 budget updated to 600.0"}

        update_budget("Utilities", "2024-06", 300.0)
        # Returns: {"message": "Budget not found for Utilities in 2024-06"}
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            UPDATE budgets
            SET monthly_limit = ?
            WHERE category = ? AND month = ?
        """, (new_limit, category, month))

        await conn.commit()

        if cursor.rowcount == 0:
            return {"message": f"Budget not found for {category} in {month}"}

        return {"message": f"{category}'s {month} budget updated to {new_limit}"}


@mcp.tool
async def list_over_budget_details():
    """
    Retrieve detailed information for all budget categories that have exceeded their limit.

    Scans every configured budget, computes total spending for each, and returns
    only those where spending has reached or exceeded 100% of the monthly limit.

    Returns:
        list[dict]: A list of over-budget entries, each containing:
            - category (str): The expense category.
            - month (str): The budget month.
            - monthly_limit (float): The configured spending limit.
            - spent (float): Total amount spent for the category and month.
            - exceeded_by (float): Amount by which spending surpassed the limit, rounded to 2 decimal places.
            - percentage_used (float): Budget consumption percentage, rounded to 2 decimal places.

        If all categories are within their limits, returns:
            {"message": "All categories are within budget!"}

        If no budgets have been configured, returns:
            {"message": "No budgets have been configured yet."}

    Example:
        list_over_budget_details()
        # Returns: [
        #     {"category": "Food", "month": "2024-06", "monthly_limit": 500.0,
        #      "spent": 620.0, "exceeded_by": 120.0, "percentage_used": 124.0},
        # ]
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            SELECT category, month, monthly_limit
            FROM budgets
        """)

        all_budgets = await cursor.fetchall()

        if not all_budgets:
            return {"message": "No budgets have been configured yet."}

        over_budget = []

        for category, month, monthly_limit in all_budgets:
            await cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE category = ?
                AND date LIKE ?
            """, (category, f"{month}%"))

            spent = (await cursor.fetchone())[0]
            percentage_used = round((spent / monthly_limit) * 100, 2) if monthly_limit > 0 else 0

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


@mcp.tool
async def budget_health_report():
    """
    Generate a high-level summary report of budget health across all categories.

    Internally calls check_budget_alerts() to evaluate every configured budget
    and aggregates the results into counts by status. Useful for a quick
    overview of overall financial health without per-category detail.

    Returns:
        dict: A summary report containing:
            - HEALTHY (int): Number of budgets with spending below 80%.
            - WARNING (int): Number of budgets with spending between 80% and 99%.
            - OVER_BUDGET (int): Number of budgets where spending has reached or exceeded 100%.
            - TOTAL_BUDGETS (int): Total number of budgets evaluated.

        If no budgets have been configured, returns:
            {"message": "No budgets have been configured yet."}

    Example:
        budget_health_report()
        # Returns: {
        #     "HEALTHY": 4,
        #     "WARNING": 2,
        #     "OVER_BUDGET": 1,
        #     "TOTAL_BUDGETS": 7
        # }
    """
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
        status = report["status"]

        if status == "HEALTHY":
            response["HEALTHY"] += 1
        elif status == "WARNING":
            response["WARNING"] += 1
        elif status == "OVER_BUDGET":
            response["OVER_BUDGET"] += 1

    response["TOTAL_BUDGETS"] = len(reports)

    return response


