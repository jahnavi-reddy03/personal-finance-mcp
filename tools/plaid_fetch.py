"""
tools/plaid_fetch.py
---------------------
Fetches real (or sandbox) transactions from Plaid and returns them in the
same JSON format as analyze_spending so all downstream tools work unchanged.

Plaid Sandbox test credentials:
  username: user_good
  password: pass_good
  Use these when linking a bank in sandbox mode.
"""

import json
from datetime import date, timedelta
from typing import Optional


# ── Category map (Plaid uses its own categories — map them to ours) ──────────
PLAID_CATEGORY_MAP: dict[str, str] = {
    "Food and Drink": "food",
    "Travel": "transport",
    "Transportation": "transport",
    "Shops": "shopping",
    "Recreation": "entertainment",
    "Entertainment": "entertainment",
    "Healthcare": "healthcare",
    "Medical": "healthcare",
    "Service": "subscriptions",
    "Payment": "housing",
    "Transfer": "income",
    "Deposit": "income",
    "Payroll": "income",
    "Bank Fees": "other",
    "Community": "other",
    "Government and Non-Profit": "other",
    "Religious": "other",
}


def map_category(plaid_categories: list[str]) -> str:
    if not plaid_categories:
        return "other"
    primary = plaid_categories[0]
    return PLAID_CATEGORY_MAP.get(primary, "other")


def run(
    access_token: str,
    plaid_client_id: str,
    plaid_secret: str,
    days: int = 30,
    environment: str = "sandbox",
) -> str:
    try:
        import plaid
        from plaid.api import plaid_api
        from plaid.model.transactions_get_request import TransactionsGetRequest
        from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
    except ImportError:
        return json.dumps({
            "error": "plaid package not installed. Run: pip install plaid-python"
        })

    # Configure Plaid client
    env_map = {
        "sandbox": plaid.Environment.Sandbox,
        "production": plaid.Environment.Production,
    }
    configuration = plaid.Configuration(
        host=env_map.get(environment, plaid.Environment.Sandbox),
        api_key={"clientId": plaid_client_id, "secret": plaid_secret},
    )
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    try:
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(count=500),
        )
        response = client.transactions_get(request)
        transactions = response["transactions"]
    except Exception as e:
        return json.dumps({"error": f"Plaid API error: {str(e)}"})

    # Build breakdown in the same shape as analyze_spending
    by_category: dict[str, float] = {}
    income_total = 0.0
    total_spend = 0.0

    for txn in transactions:
        amount = txn["amount"]  # Plaid: positive = expense, negative = income
        category = map_category(txn.get("category") or [])

        if amount < 0:
            # Income / refund
            income_total += abs(amount)
        else:
            total_spend += amount
            by_category[category] = by_category.get(category, 0) + amount

    breakdown = {
        cat: {
            "total": round(amt, 2),
            "pct": round((amt / total_spend * 100) if total_spend else 0, 1),
        }
        for cat, amt in sorted(by_category.items(), key=lambda x: -x[1])
    }

    result = {
        "total_transactions": len(transactions),
        "total_spend": round(total_spend, 2),
        "currency": "USD",
        "breakdown": breakdown,
        "income_total": round(income_total, 2),
        "source": f"plaid_{environment}",
        "period_days": days,
    }

    return json.dumps(result, indent=2)
