"""
tools/overspending.py
----------------------
Compares each category's spend against standard benchmarks and flags
anything that looks off. Uses the 50/30/20 rule as a top-level guide
and per-category soft limits as secondary checks.
"""

import json


# Category spend as % of monthly income (soft ceilings)
CATEGORY_PCT_BENCHMARKS: dict[str, float] = {
    "housing": 30.0,
    "food": 15.0,
    "transport": 15.0,
    "subscriptions": 5.0,
    "entertainment": 5.0,
    "shopping": 10.0,
    "healthcare": 5.0,
    "other": 5.0,
}

# Absolute monthly $ thresholds — fallback when no income data
CATEGORY_ABS_BENCHMARKS: dict[str, float] = {
    "housing": 1_800,
    "food": 600,
    "transport": 400,
    "subscriptions": 100,
    "entertainment": 150,
    "shopping": 300,
    "healthcare": 200,
    "other": 150,
}


def run(data: str) -> str:
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON. Pass the output of analyze_spending directly."})

    breakdown = parsed.get("breakdown", {})
    total_spend = parsed.get("total_spend", 0)
    income = parsed.get("income_total", 0)

    flags: list[dict] = []

    for category, info in breakdown.items():
        if category == "income":
            continue

        amt = info.get("total", 0)
        benchmark_pct = CATEGORY_PCT_BENCHMARKS.get(category)
        benchmark_abs = CATEGORY_ABS_BENCHMARKS.get(category)
        flagged = False
        reason = ""

        if income and benchmark_pct:
            actual_pct = (amt / income) * 100
            if actual_pct > benchmark_pct:
                flagged = True
                reason = (
                    f"{actual_pct:.1f}% of income "
                    f"(guideline: ≤{benchmark_pct}%)"
                )
        elif benchmark_abs and amt > benchmark_abs:
            flagged = True
            reason = f"${amt:.0f} exceeds the ${benchmark_abs:.0f}/mo soft limit"

        if flagged:
            flags.append({
                "category": category,
                "amount": round(amt, 2),
                "reason": reason,
                "next_step": f"Run get_savings_tips('{category}') for personalized ideas.",
            })

    verdict = (
        f"{len(flags)} category/categories flagged for review."
        if flags
        else "Spending looks healthy across all categories."
    )

    return json.dumps(
        {"verdict": verdict, "flags": flags, "total_spend": total_spend},
        indent=2,
    )
