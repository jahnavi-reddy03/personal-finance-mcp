# Personal Finance MCP Server

> *"Wait, where did my money go this month?"*

We've all been there. You check your bank balance at the end of the month and it's somehow $400 less than you expected. You open your transactions, scroll for five minutes, and still can't figure out what happened.

This project fixes that — by giving Claude the ability to actually analyze your finances. Not just read numbers, but understand them, flag the problems, and tell you exactly what to do differently.

![Demo](docs/demo.gif)

---

## The idea

Most finance apps are dashboards you have to go *to*. This is different — it's an MCP server that plugs directly into Claude Desktop, so your AI assistant gains finance analysis as a native ability. You just talk to it.

```
"Analyze my spending from last month and tell me where I'm bleeding money."
```

Claude pulls your transactions, categorizes everything, compares it against the 50/30/20 rule, surfaces the problem areas, and gives you a plain-English report with actionable tips — all in one response, no spreadsheets, no dashboards.

---

## What's under the hood

Five tools that chain together:

| Tool | What it actually does |
|------|-----------------------|
| `analyze_spending` | Reads your bank CSV, categorizes every transaction by keyword matching, returns totals + percentages per category |
| `flag_overspending` | Compares each category against standard benchmarks (30% housing, 15% food, etc.) and flags anything over the limit |
| `get_savings_tips` | Calls GPT-3.5 to generate 5 specific, actionable tips for whichever category is hurting you |
| `generate_report` | Writes a plain-English monthly finance summary — highlights, red flags, and a one-line verdict |
| `fetch_bank_transactions` | Connects to real bank accounts via Plaid and pulls live transactions — same output format, so all other tools work on it automatically |

---

## Real bank data via Plaid

The CSV flow works with any bank export. But if you want *live* data, the Plaid integration connects to actual bank accounts (Chase, BofA, Wells Fargo, 12,000+ others) and pulls real transactions in real time.

For testing, Plaid's sandbox gives you a fake-but-realistic bank with pre-loaded transactions — no real account needed.

---

## Get it running

**1. Clone and set up:**
```bash
git clone https://github.com/jahnavi-reddy03/personal-finance-mcp.git
cd personal-finance-mcp
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

**2. Add your API keys:**
```bash
cp .env.example .env
# then edit .env and fill in your OpenAI + Plaid keys
```

**3. Wire it into Claude Desktop** — add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "personal-finance": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\personal-finance-mcp\\server.py"]
    }
  }
}
```

Restart Claude Desktop. The five tools load automatically — you'll see them in Settings → Developer → Local MCP Servers.

---

## Try it yourself

There's a 30-transaction sample CSV in `data/sample/transactions.csv` so you can test immediately without connecting a bank. Just paste this into Claude Desktop:

```
Analyze my spending from C:\path\to\personal-finance-mcp\data\sample\transactions.csv,
flag anything over budget, and give me a full report with savings tips.
```

For live Plaid data, run the helper script first to get a sandbox access token:
```bash
python get_sandbox_token.py
```

---

## Tech stack

- **Python + FastMCP** — the MCP server itself and all tool definitions
- **Pandas** — transaction parsing, categorization, and aggregation
- **OpenAI GPT-3.5** — generates tips and report narrative (falls back to static tips if no API key)
- **Plaid API** — live bank transaction fetching across 12,000+ institutions
- **python-dotenv** — keeps API keys out of the codebase

---

## Project structure

```
personal-finance-mcp/
├── server.py              ← entry point, all 5 tools registered here
├── tools/
│   ├── analyze.py         ← CSV parsing + keyword categorization
│   ├── overspending.py    ← 50/30/20 benchmark comparisons
│   ├── tips.py            ← GPT-3.5 tips + static fallback
│   ├── report.py          ← plain-English report generator
│   └── plaid_fetch.py     ← live bank data via Plaid
├── data/sample/
│   └── transactions.csv   ← 30 realistic test transactions
├── get_sandbox_token.py   ← one-time script to get Plaid sandbox token
├── .env.example           ← copy this to .env, never commit .env
└── requirements.txt
```

---

## Built by

**Jahnavi Reddy** — F-1 OPT, AI Engineer  
[github.com/jahnavi-reddy03](https://github.com/jahnavi-reddy03)

This is Project 2 of my AI engineering portfolio. Project 1 — a Security Threat Intelligence RAG system with 60% hallucination reduction — is live at [ai-security-rag.streamlit.app](https://ai-security-rag.streamlit.app).

---

## License

MIT — use it, fork it, build on it.
