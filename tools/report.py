"""
tools/report.py
----------------
Generates a plain-English monthly finance report from the spending breakdown.
Uses GPT-3.5-turbo when an API key is available; falls back to a template
renderer otherwise.
"""

import json
from typing import Optional


def run(data: str, api_key: Optional[str] = None) -> str:
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON. Pass the output of analyze_spending directly."})

    if api_key:
        try:
            return _gpt_report(parsed, api_key)
        except Exception:
            pass  # fall through to template

    return _template_report(parsed)


# ── GPT-3.5 report ────────────────────────────────────────────────────────────

def _gpt_report(parsed: dict, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    summary = json.dumps(parsed, indent=2)
    prompt = (
        "Here is a monthly spending breakdown in JSON format:\n\n"
        f"{summary}\n\n"
        "Write a concise personal finance report (200-250 words) covering:\n"
        "1. Top spending categories and whether they look reasonable\n"
        "2. Any red flags or areas of concern\n"
        "3. One concrete thing to do differently next month\n"
        "4. A one-sentence overall verdict\n\n"
        "Write in a direct, friendly tone — like a smart friend who's good with money, "
        "not a formal financial advisor. No bullet points; just clear paragraphs."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal finance coach who gives honest, "
                    "practical feedback without sugarcoating."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )

    report_text = response.choices[0].message.content.strip()
    return json.dumps({"report": report_text, "source": "gpt-3.5-turbo"}, indent=2)


# ── Template fallback ─────────────────────────────────────────────────────────

def _template_report(parsed: dict) -> str:
    total = parsed.get("total_spend", 0)
    income = parsed.get("income_total", 0)
    breakdown = parsed.get("breakdown", {})

    top = sorted(breakdown.items(), key=lambda x: x[1]["total"], reverse=True)[:3]
    top_lines = ", ".join(
        f"{cat} (${info['total']:.0f}, {info['pct']}%)" for cat, info in top
    )

    savings_rate = ""
    if income > 0:
        net = income - total
        rate = (net / income) * 100
        savings_rate = f" With ${income:.0f} in income, your estimated savings rate is {rate:.1f}%."

    high_flags = [
        cat for cat, info in breakdown.items()
        if info.get("pct", 0) > 20 and cat != "housing"
    ]
    flag_line = (
        f" Watch out for {', '.join(high_flags)} — those percentages are on the high side."
        if high_flags else ""
    )

    report = (
        f"Monthly Finance Report\n"
        f"{'─' * 40}\n\n"
        f"Total spend this month: ${total:.2f}.{savings_rate}\n\n"
        f"Your biggest spending categories were {top_lines}.\n"
        f"{flag_line}\n\n"
        f"Verdict: {'You have room to tighten up in a few areas.' if high_flags else 'Your spending distribution looks reasonable.'} "
        f"Run get_savings_tips() on any category you want to trim."
    )

    return json.dumps({"report": report.strip(), "source": "template"}, indent=2)
