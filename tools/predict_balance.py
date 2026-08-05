"""
tools/predict_balance.py
-------------------------
Projects future balance month-by-month based on current income and spending.
Also computes a year-end forecast and savings rate.

Input:  JSON string (output of analyze_spending or fetch_bank_transactions)
Output: JSON with month-by-month projection, year-end balance, savings rate,
        and a plain-English verdict.
"""

import json
from datetime import date


# Static fallback verdicts based on savings rate
def _verdict(savings_rate: float, monthly_surplus: float) -> str:
    if savings_rate >= 20:
        return (
            f"You're saving {savings_rate:.1f}% of your income — above the 20% benchmark. "
            f"At this rate you'll add ${monthly_surplus * 12:,.0f} to your savings by year-end."
        )
    elif savings_rate >= 10:
        return (
            f"You're saving {savings_rate:.1f}% of your income — decent, but below the 20% goal. "
            f"Cutting one major category could close that gap."
        )
    elif savings_rate > 0:
        return (
            f"You're saving only {savings_rate:.1f}% of your income. "
            f"At this pace you'll save ${monthly_surplus * 12:,.0f} over the year — "
            f"worth reviewing your top two spending categories."
        )
    else:
        return (
            f"You're spending more than you earn this month (deficit: ${abs(monthly_surplus):,.0f}). "
            f"This is not sustainable — immediate budget review recommended."
        )


def run(data: str, months: int = 12, current_savings: float = 0.0) -> str:
    """
    data            : JSON string from analyze_spending or fetch_bank_transactions
    months          : how many months to project forward (default 12)
    current_savings : your current savings balance to build on (default 0)
    """
    try:
        d = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"error": "Invalid input — pass the JSON output of analyze_spending."})

    income = float(d.get("income_total", 0))
    spend  = float(d.get("total_spend", 0))

    if income == 0:
        return json.dumps({
            "error": (
                "No income found in the data. Make sure your CSV includes income transactions "
                "(positive amounts) or that your Plaid data includes payroll entries."
            )
        })

    monthly_surplus = income - spend
    savings_rate    = (monthly_surplus / income * 100) if income > 0 else 0

    # Month-by-month projection
    today = date.today()
    projection = []
    balance = current_savings

    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    for i in range(1, months + 1):
        balance += monthly_surplus
        month_idx = (today.month - 1 + i) % 12
        year_offset = (today.month - 1 + i) // 12
        projection.append({
            "month": f"{month_names[month_idx]} {today.year + year_offset}",
            "projected_balance": round(balance, 2),
            "monthly_surplus": round(monthly_surplus, 2),
        })

    year_end_balance = current_savings + (monthly_surplus * months)

    result = {
        "income_per_month":    round(income, 2),
        "spend_per_month":     round(spend, 2),
        "monthly_surplus":     round(monthly_surplus, 2),
        "savings_rate_pct":    round(savings_rate, 1),
        "current_savings":     round(current_savings, 2),
        "projected_months":    months,
        "year_end_balance":    round(year_end_balance, 2),
        "month_by_month":      projection,
        "verdict":             _verdict(savings_rate, monthly_surplus),
    }

    return json.dumps(result, indent=2)
