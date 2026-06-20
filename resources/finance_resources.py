from datetime import datetime

from mcp_instance import mcp

from tools.income_tools import (
    financial_summary,
    highest_income_source
)

from tools.expense_tools import (
    highest_spending_category_by_month
)

from tools.budget_tool import (
    budget_health_report
)


@mcp.resource("finance://dashboard")
async def finance_dashboard():
    """
    MCP resource that provides a real-time financial dashboard
    for the current month.
    """

    month = datetime.now().strftime("%Y-%m")

    summary = await financial_summary(month)
    budget_health = await budget_health_report()

    return {
        "month": month,
        "total_income": summary["total_income"],
        "total_expenses": summary["total_expenses"],
        "net_savings": summary["net_savings"],
        "savings_rate": summary["savings_rate"],
        "budget_health": budget_health
    }


@mcp.resource("finance://monthly-report")
async def monthly_report():
    """
    MCP resource that provides a detailed monthly financial report.

    Resource URI:
        finance://monthly-report

    Returns:
        dict containing:
            - month
            - total income
            - total expenses
            - net savings
            - savings rate
            - highest income source
            - highest spending category
            - budget health
    """

    month = datetime.now().strftime("%Y-%m")

    summary = await financial_summary(month)

    highest_income = await highest_income_source()

    highest_spending = await highest_spending_category_by_month(month)

    budget_health = await budget_health_report()

    return {
        "month": month,
        "total_income": summary["total_income"],
        "total_expenses": summary["total_expenses"],
        "net_savings": summary["net_savings"],
        "savings_rate": summary["savings_rate"],
        "highest_income_source": highest_income,
        "highest_spending_category": highest_spending,
        "budget_health": budget_health
    }


