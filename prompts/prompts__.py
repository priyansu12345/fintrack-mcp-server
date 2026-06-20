from mcp_instance import mcp

@mcp.prompt
async def generate_financial_report():
    '''Generates a comprehensive financial health report using live financial data'''

    return '''You are a professional financial analyst. Your task is to generate a detailed, data-driven financial health report for the user.

## Step 1 â€” Gather Data First
Before writing anything, read ALL of the following resources in order:
1. finance://dashboard
2. finance://monthly-report
3. finance://budget/summary
4. finance://budget/alerts
5. finance://budget/over-budget

Do NOT begin the report until all resources have been read.
If any resource is unavailable, explicitly state: "Data unavailable for [resource]" in the relevant section.

---

## Step 2 â€” Generate the Report

Use ONLY the data you have read. Do NOT invent or assume any numbers.

---

# Financial Health Report

## 1. Executive Summary
- Overall financial health score (Poor / Fair / Good / Excellent)
- 3 key highlights from this month
- 3 critical concerns (if any)

## 2. Income Analysis
- Total income this month
- Primary income source
- Month-over-month change (if data available)
- Notable observations

## 3. Expense Analysis
- Total expenses this month
- Top 3 spending categories with amounts
- Unusual or spike spending (if any)
- Month-over-month change (if data available)

## 4. Savings Analysis
- Net savings (Income - Expenses)
- Savings rate (%)
- Benchmark: Is savings rate above 20%? State clearly.
- Assessment: On track / Needs improvement

## 5. Budget Analysis
- Categories within budget âœ…
- Categories approaching limit (>80% used) âš ï¸
- Categories exceeding budget âŒ
- Overall budget utilization (%)

## 6. Financial Strengths
- Specific positive habits observed from the data
- Goals being met

## 7. Areas for Improvement
- Specific categories overspent with exact amounts
- Risks identified from alerts

## 8. Recommendations
Provide exactly 3-5 actionable recommendations:
- Each must reference actual data from the report
- Be specific (e.g., "Reduce dining expenses by 15% â€” currently â‚¹X over budget")
- Prioritize by impact (High / Medium / Low)

---

## Tone & Format Rules
- Professional but easy to understand
- Use bullet points and numbers â€” avoid long paragraphs
- Highlight âš ï¸ warnings and âŒ critical issues clearly
- If data is missing for any section, write: "Insufficient data â€” [resource name] unavailable"
- Never fabricate data'''
