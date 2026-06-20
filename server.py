import asyncio

from mcp_instance import mcp
from database import init_db
import tools.expense_tools
import tools.budget_tool
import tools.income_tools
import resources.expense_resources
import resources.budget_resources
import resources.finance_resources
import prompts.prompts__

async def main():
    await init_db()
    await mcp.run_async(transport="streamable-http")


if __name__ == "__main__":
    asyncio.run(main())
