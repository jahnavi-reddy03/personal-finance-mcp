"""
tools/savings_plan.py
----------------------
Generates a prioritized 3-month savings plan using GPT-3.5.
Falls back to a rule-based plan if no API key is available.

Input:  JSON string (output of analyze_spending or fetch_bank_transactions)
        + optional target_monthly_savings (float)
Output: JSON with plan (text), suggested cuts per category, projected outcome
"""

import json


STATIC_CUTS = {
    "food":          ("Cut food spend by 20%", "Meal prep 3x per week, limit delivery to once a week."),
    "transport":     ("Reduce transport by 15%", "Use public transit for commutes, batch errands into one trip."),
    "subscriptions": ("Audit subscriptions", "Cancel any service you haven't used in the last 30 days."),
    "entertainment": ("Cap entertainment", "Set a fixed weekly fun budget and stick to it."),
    "shopping":      ("Add a 48-hour rule", "Wait 48 hours before any non-essential purchase over $30."),
    "housing":       ("Review housing costs", "Negotiate rent at renewal, or look into a roommate."),
    "healthcare":    ("Use generics", "Ask your doctor for generic prescriptions — usually 60-80% cheaper."),
    "other":         ("Track miscellaneous", "Log every 'other' expense for one week to find hidden patterns."),
}


def _static_plan(spend_breakdown: dict, income: float, target: float) -> dict:
    surplus = income - sum(c["total"] for c in spend_breakdown.values())
    gap     = max(0, target - surplus)

    cuts = []
    for cat, data in sorted(spend_breakdown.items(), key=lambda x: -x[1]["total"]):
        if cat == "income":
            continue
        headline, tip = STATIC_CUTS.get(cat, ("Review " + cat, "Look for ways to reduce this category."))
        potential = round(data["total"] * 0.15, 2)
        cuts.append({
            "category":        cat,
            "current_spend":   data["total"],
            "suggested_cut":   potential,
            "action":          headline,
            "tip":             tip,
        })

    plan_lines = [
        f"Based on your current spending, here's a 3-month plan to boost your savings:",
        "",
        f"Current monthly surplus: ${surplus:,.2f}",
        f"Target monthly savings:  ${target:,.2f}",
        f"Gap to close:            ${gap:,.2f}",
        "",
        "Priority cuts:",
    ]
    for c in cuts[:3]:
        plan_lines.append(f"  • {c['category'].title()} — {c['action']} (saves ~${c['suggested_cut']:,.2f}/mo)")
        plan_lines.append(f"    {c['tip']}")

    plan_lines += [
        "",
        "If you follow these cuts for 3 months:",
        f"  Month 1 target: ${target:,.2f} saved",
        f"  Month 3 total:  ${target * 3:,.2f} saved",
    ]

    return {
        "source":              "rule-based",
        "current_surplus":     round(surplus, 2),
        "target_monthly":      round(target, 2),
        "gap_to_close":        round(gap, 2),
        "suggested_cuts":      cuts[:5],
        "plan":                "\n".join(plan_lines),
        "3_month_projection":  round(target * 3, 2),
    }


def _gpt_plan(data: dict, target: float, api_key: str) -> dict:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        income    = data.get("income_total", 0)
        spend     = data.get("total_spend", 0)
        breakdown = data.get("breakdown", {})

        breakdown_text = "\n".join(
            f"  {cat}: ${vals['total']:.2f} ({vals['pct']}% of spend)"
            for cat, vals in breakdown.items()
        )

        prompt = f"""You are a personal finance advisor. A user's monthly finances are:

Income: ${income:.2f}
Total spend: ${spend:.2f}
Monthly surplus: ${income - spend:.2f}
Target monthly savings: ${target:.2f}

Spending breakdown:
{breakdown_text}

Write a practical, friendly 3-month savings plan. Be specific — name the exact categories to cut and by how much.
Give 3-4 concrete actions. End with what their savings will look like after 3 months if they follow the plan.
Keep it under 250 words. No bullet overload — write in short paragraphs."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )

        plan_text = response.choices[0].message.content.strip()
        surplus   = income - spend
        gap       = max(0, target - surplus)

        return {
            "source":             "gpt-3.5-turbo",
            "current_surplus":    round(surplus, 2),
            "target_monthly":     round(target, 2),
            "gap_to_close":       round(gap, 2),
            "plan":               plan_text,
            "3_month_projection": round(target * 3, 2),
        }

    except Exception as e:
        return None


def run(data: str, target_monthly_savings: float = 500.0, api_key: str = None) -> str:
    """
    data                   : JSON string from analyze_spending or fetch_bank_transactions
    target_monthly_savings : how much you want to save per month (default $500)
    api_key                : OpenAI API key (optional — falls back to rule-based plan)
    """
    try:
        d = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"error": "Invalid input — pass the JSON output of analyze_spending."})

    income    = float(d.get("income_total", 0))
    breakdown = d.get("breakdown", {})

    if income == 0:
        return json.dumps({
            "error": "No income found. Include income transactions in your CSV for a personalized plan."
        })

    target = float(target_monthly_savings)

    # Try GPT first
    if api_key:
        result = _gpt_plan(d, target, api_key)
        if result:
            return json.dumps(result, indent=2)

    # Fallback to rule-based
    result = _static_plan(breakdown, income, target)
    return json.dumps(result, indent=2)
