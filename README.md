# 💰 FinTrack MCP Server

> A production-ready Remote MCP Server for Personal Finance Management, Budget Tracking, Income Analytics, and Financial Reporting.

FinTrack MCP enables AI assistants and MCP-compatible clients to manage personal finances through tools, resources, and prompts. The server provides expense tracking, budget monitoring, income management, savings analysis, and comprehensive financial reporting.

---

# 🌍 Remote MCP Server

FinTrack is deployed as a remote MCP server and can be accessed directly by any MCP-compatible client.

### Server URL

```text
https://fintrack-mcp-server.fastmcp.app/mcp
```

### MCP Configuration

```json
{
  "mcpServers": {
    "fintrack-mcp": {
      "url": "https://fintrack-mcp-server.fastmcp.app/mcp"
    }
  }
}
```

No local installation is required to use the deployed server.

---

# ✨ Features

## 📊 Expense Management

* Add expenses
* Update expenses
* Delete expenses
* View expenses
* Category-wise expense analysis
* Date range filtering
* Expense summaries
* Highest spending category detection

## 💵 Income Management

* Add income records
* Update income records
* Delete income records
* Income source tracking
* Income analytics
* Highest income source identification

## 🎯 Budget Management

* Create monthly budgets
* Update budget limits
* Delete budgets
* Budget utilization tracking
* Budget alerts
* Over-budget detection
* Budget health reporting

## 📈 Financial Analytics

* Monthly savings calculation
* Savings rate analysis
* Financial summaries
* Cash flow tracking
* Financial health assessment

## 🧠 MCP Resources

### Expense Resources

```text
expense://summary
expense://count
```

### Budget Resources

```text
budget://summary
budget://alerts
budget://over-budget
```

### Finance Resources

```text
finance://dashboard
finance://monthly-report
```

## 🤖 MCP Prompts

### Financial Health Report

Generates a detailed report including:

* Income analysis
* Expense analysis
* Savings analysis
* Budget health assessment
* Financial recommendations

---

# 🏗️ Architecture

```text
User
 │
 ▼
MCP Client
(ChatGPT / Claude / Cursor / VS Code)
 │
 ▼
FinTrack MCP Server
 │
 ├── Expense Tools
 ├── Income Tools
 ├── Budget Tools
 ├── Resources
 └── Prompts
 │
 ▼
PostgreSQL Database
(Neon.tech - Cloud Hosted)
```

---

# 🛠️ Tech Stack

| Technology | Purpose                 |
| ---------- | ----------------------- |
| Python     | Backend Development     |
| FastMCP    | MCP Server Framework    |
| PostgreSQL | Data Storage (Neon.tech)|
| AsyncPG    | Async PostgreSQL Driver |
| AsyncIO    | Asynchronous Operations |

---

# 📂 Project Structure

```text
fintrack-mcp-server/
│
├── tools/
│   ├── expense_tools.py
│   ├── income_tools.py
│   └── budget_tool.py
│
├── resources/
│   ├── expense_resources.py
│   ├── budget_resources.py
│   └── finance_resources.py
│
├── prompts/
│   └── financial_health_report.py
│
├── database.py
├── mcp_instance.py
├── server.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🚀 Local Development Setup

## Clone Repository

```bash
git clone https://github.com/priyansu12345/fintrack-mcp-server.git
cd fintrack-mcp-server
```

## Create Virtual Environment

```bash
python -m venv .venv
```

## Activate Environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file or set the following environment variable:

```bash
DATABASE_URL=postgresql://username:password@ep-xxx.neon.tech/neondb?sslmode=require
```

> Get your free PostgreSQL database at [neon.tech](https://neon.tech)

## Run Server

```bash
python server.py
```

---

# 📋 Example User Queries

## Expense Tracking

```text
I spent ₹150 on a paneer roll today.
```

```text
Show all my expenses.
```

```text
Which category am I spending the most on this month?
```

## Budget Management

```text
Set a food budget of ₹10,000 for this month.
```

```text
How much food budget do I have left?
```

```text
Which categories are over budget?
```

## Income Tracking

```text
My salary of ₹50,000 was credited today.
```

```text
Show all my income records.
```

```text
What is my highest income source this month?
```

## Financial Analysis

```text
How much have I saved this month?
```

```text
Give me a complete financial summary.
```

```text
Generate a detailed financial health report.
```

---

# 🎯 Supported Capabilities

✅ Expense Tracking

✅ Budget Monitoring

✅ Income Management

✅ Savings Analytics

✅ Financial Reporting

✅ Resource-Based Context Retrieval

✅ MCP Prompt Support

✅ Remote MCP Deployment

✅ Async Architecture

✅ Cloud PostgreSQL (Persistent Storage)

---

# 👨‍💻 Author

**Priyanshu Kumar**

Built to explore and demonstrate the capabilities of the Model Context Protocol (MCP), including tools, resources, prompts, and remote server deployment.

---

# ⭐ Support

If you found this project useful, consider giving it a star on GitHub.

```bash
⭐ Star the repository
🍴 Fork the project
🚀 Build something awesome with MCP
```
