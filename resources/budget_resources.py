from mcp_instance import mcp
from database import get_connection
from tools.budget_tool import budget_health_report, check_budget_alerts, list_over_budget_details


@mcp.resource("budget://summary")
async def budget_summary():
    """
    MCP resource that provides a high-level health summary of all configured budgets.

    Resource URI:
        budget://summary

    Delegates to `budget_health_report()` which aggregates all budget statuses
    into counts by health category (HEALTHY, WARNING, OVER_BUDGET).

    Returns:
        dict: A summary report containing:
            - HEALTHY (int): Number of budgets with spending below 80%.
            - WARNING (int): Number of budgets with spending between 80% and 99%.
            - OVER_BUDGET (int): Number of budgets where spending has reached or exceeded 100%.
            - TOTAL_BUDGETS (int): Total number of budgets evaluated.

        If no budgets are configured, returns:
            {"message": "No budgets have been configured yet."}

    Example:
        # Accessing budget://summary returns:
        {
            "HEALTHY": 4,
            "WARNING": 2,
            "OVER_BUDGET": 1,
            "TOTAL_BUDGETS": 7
        }
    """
    return await budget_health_report()


@mcp.resource("budget://alerts")
async def budget_alert():
    """
    MCP resource that returns per-budget alert statuses based on spending thresholds.

    Resource URI:
        budget://alerts

    Delegates to `check_budget_alerts()` which evaluates every configured budget
    against actual expenses and assigns an alert level to each:
        - 'HEALTHY'     : Less than 80% of the budget has been spent.
        - 'WARNING'     : Between 80% and 99% of the budget has been spent.
        - 'OVER_BUDGET' : 100% or more of the budget has been spent.

    Returns:
        list[dict]: A list of alert entries, one per budget, each containing:
            - category (str): The expense category.
            - month (str): The budget month in 'YYYY-MM' format.
            - monthly_limit (float): The configured spending limit.
            - spent (float): Total amount spent for the category and month.
            - remaining (float): Remaining balance; negative if over budget.
            - percentage_used (float): Budget consumption percentage, rounded to 2 decimal places.
            - status (str): One of 'HEALTHY', 'WARNING', or 'OVER_BUDGET'.

        If no budgets are configured, returns:
            {"message": "No budgets have been configured yet."}

    Example:
        # Accessing budget://alerts returns:
        [
            {
                "category": "Food", "month": "2024-06", "monthly_limit": 500.0,
                "spent": 420.0, "remaining": 80.0, "percentage_used": 84.0,
                "status": "WARNING"
            },
            {
                "category": "Transport", "month": "2024-06", "monthly_limit": 200.0,
                "spent": 90.0, "remaining": 110.0, "percentage_used": 45.0,
                "status": "HEALTHY"
            }
        ]
    """
    return await check_budget_alerts()


@mcp.resource("budget://over-budget")
async def over_budget():
    """
    MCP resource that lists all budget categories that have exceeded their monthly limit.

    Resource URI:
        budget://over-budget

    Delegates to `list_over_budget_categories()` which scans all configured budgets
    and returns only those where spending has reached or surpassed 100% of the limit.

    Returns:
        list[dict]: A list of over-budget entries, each containing:
            - category (str): The expense category.
            - month (str): The budget month in 'YYYY-MM' format.
            - monthly_limit (float): The configured spending limit.
            - spent (float): Total amount spent for the category and month.
            - exceeded_by (float): Amount by which spending surpassed the limit, rounded to 2 decimal places.
            - percentage_used (float): Budget consumption percentage, rounded to 2 decimal places.

        If all categories are within their limits, returns:
            {"message": "All categories are within budget!"}

        If no budgets have been configured, returns:
            {"message": "No budgets have been configured yet."}

    Example:
        # Accessing budget://over-budget returns:
        [
            {
                "category": "Food", "month": "2024-06", "monthly_limit": 500.0,
                "spent": 620.0, "exceeded_by": 120.0, "percentage_used": 124.0
            }
        ]
    """
    return await list_over_budget_details()


