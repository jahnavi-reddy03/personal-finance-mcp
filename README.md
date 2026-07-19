# Personal Finance MCP Server

An MCP (Model Context Protocol) server that gives AI assistants real-time personal finance superpowers. Plug it into Claude Desktop and just ask — it analyzes your spending, flags problem areas, fetches live bank data via Plaid, and generates plain-English reports automatically.

![Demo](docs/demo.gif)

---

## What it does

Five tools, one goal — understand your money without opening a spreadsheet:

| Tool | What it does |
|------|-------------|
| `analyze_spending` | Loads a bank CSV, categorizes every transaction, returns totals by category |
| `flag_overspending` | Compares your spending against the 50/30/20 rule and flags problem areas |
| `get_savings_tips` | Returns 5 personalized tips per category via GPT-3.5 |
| `generate_report` | Produces a plain-English monthly finance report |
| `fetch_bank_transactions` | Pulls live transactions from any bank via Plaid (sandbox + production) |

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/jahnavi-reddy03/personal-finance-mcp.git
cd personal-finance-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-...
PLAID_CLIENT_ID=your-client-id
PLAID_SECRET=your-sandbox-secret
PLAID_ENV=sandbox
```

### 3. Add to Claude Desktop

Edit `claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "personal-finance": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/personal-finance-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop. The tools load automatically.

---

## Usage

**CSV analysis (works with any bank export):**
```
Analyze my spending from /path/to/transactions.csv, flag overspending,
and generate a report with savings tips for the worst category.
```

**Live bank data via Plaid:**
```
Fetch my bank transactions using access token <your-token> and tell me
where I'm overspending this month.
```

**Expected CSV format:**
```
date,description,amount
2024-06-01,Direct Deposit,3200.00
2024-06-03,Whole Foods,-87.50
2024-06-05,Netflix,-15.99
```
Negative amounts = expenses, positive = income.

---

## Tech stack

- **Python** + **MCP SDK** (FastMCP) — server and tool definitions
- **Pandas** — transaction parsing and categorization
- **OpenAI GPT-3.5** — personalized savings tips and report generation
- **Plaid API** — live bank transaction fetching (sandbox + production)
- **python-dotenv** — secure API key management

---

## Project structure

```
personal-finance-mcp/
├── server.py              # MCP server — all 5 tools registered
├── tools/
│   ├── analyze.py         # CSV categorization + spending breakdown
│   ├── overspending.py    # 50/30/20 benchmark comparison
│   ├── tips.py            # GPT-3.5 savings tips (static fallback)
│   ├── report.py          # Plain-English monthly report
│   └── plaid_fetch.py     # Live bank data via Plaid
├── data/sample/
│   └── transactions.csv   # 30 realistic test transactions
├── get_sandbox_token.py   # Helper to get Plaid sandbox token
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Categorization logic

Transactions are auto-categorized using keyword matching across 8 categories: food, transport, housing, subscriptions, healthcare, entertainment, shopping, and income. The Plaid integration maps Plaid's own category system to the same 8 categories so all downstream tools work identically regardless of data source.

---

## Author

**Jahnavi Reddy** — [github.com/jahnavi-reddy03](https://github.com/jahnavi-reddy03)

Built as part of an AI engineering portfolio. See also: [Security Threat Intelligence RAG System](https://github.com/jahnavi-reddy03/ai-security-rag).

---

## License

MIT
