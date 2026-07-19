"""
Personal Finance MCP Server
----------------------------
Plug this into Claude Desktop or Cursor and your AI instantly gets
four finance-analysis superpowers.

Run locally:
    python server.py

Claude Desktop claude_desktop_config.json snippet:
{
  "mcpServers": {
    "personal-finance": {
      "command": "python",
      "args": ["/absolute/path/to/personal-finance-mcp/server.py"]
    }
  }
}
"""

import os
import sys

# Ensure the project root is on the path so `tools` package is always found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Pre-import tools so errors surface at startup, not mid-call
from tools.analyze import run as _analyze
from tools.overspending import run as _overspending
from tools.tips import run as _tips
from tools.report import run as _report

# Load API keys from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ── MCP server ──────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="personal-finance",
    instructions=(
        "You are a personal finance assistant. Use these tools to analyze "
        "spending, flag problem areas, surface savings tips, and generate "
        "plain-English finance reports."
    ),
)

# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def analyze_spending(csv_path: str) -> str:
    """
    Load a bank/credit-card CSV, categorize every transaction, and return
    a breakdown of spending by category with totals and percentages.

    Args:
        csv_path: Absolute path to the transaction CSV file.
                  Expected columns: date, description, amount
                  (negative = expense, positive = income).
    """
    return _analyze(csv_path)


@mcp.tool()
def flag_overspending(data: str) -> str:
    """
    Compare category totals against standard benchmarks (50/30/20 rule +
    category-level guidelines) and flag any area where spending looks high.

    Args:
        data: JSON string produced by analyze_spending, or a dict-like
              mapping of {category: total_amount}.
    """
    return _overspending(data)


@mcp.tool()
def get_savings_tips(category: str) -> str:
    """
    Return 3-5 concrete, personalized savings tips for a given spending
    category. Uses GPT-3.5 to keep advice fresh and specific.

    Args:
        category: e.g. "food", "transport", "subscriptions", "housing",
                  "entertainment", "healthcare", "shopping".
    """
    return _tips(category, api_key=OPENAI_API_KEY)


@mcp.tool()
def generate_report(data: str) -> str:
    """
    Take the full spending breakdown and produce a concise, plain-English
    monthly finance report: highlights, red flags, and a one-line verdict.

    Args:
        data: JSON string produced by analyze_spending.
    """
    return _report(data, api_key=OPENAI_API_KEY)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
