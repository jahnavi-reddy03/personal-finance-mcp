"""
tools/analyze.py
-----------------
Loads a transaction CSV, auto-categorizes every row using keyword matching,
and returns a JSON summary with per-category totals and percentages.
"""

import json
import pandas as pd


# ── Keyword → category map ────────────────────────────────────────────────────
CATEGORY_RULES: dict[str, list[str]] = {
    "food": [
        "restaurant", "cafe", "coffee", "starbucks", "mcdonalds", "chipotle",
        "doordash", "ubereats", "grubhub", "pizza", "sushi", "taco", "burrito",
        "grocery", "whole foods", "trader joe", "safeway", "kroger", "aldi",
        "walmart grocery", "instacart", "diner", "bakery", "smoothie",
    ],
    "transport": [
        "uber", "lyft", "taxi", "subway", "metro", "mta", "bart", "transit",
        "gas station", "shell", "chevron", "bp", "exxon", "parking", "toll",
        "zipcar", "enterprise", "hertz", "amtrak", "greyhound",
    ],
    "housing": [
        "rent", "mortgage", "lease", "apartment", "electric", "water",
        "utility", "pg&e", "con ed", "internet", "comcast", "xfinity",
        "att", "verizon home", "spectrum",
    ],
    "subscriptions": [
        "netflix", "hulu", "disney", "spotify", "apple music", "amazon prime",
        "youtube", "hbo", "peacock", "paramount", "adobe", "microsoft 365",
        "dropbox", "github", "notion", "slack", "duolingo", "headspace",
    ],
    "healthcare": [
        "pharmacy", "cvs", "walgreens", "rite aid", "hospital", "clinic",
        "doctor", "dentist", "optometrist", "insurance", "copay", "lab",
        "urgent care", "therapy",
    ],
    "entertainment": [
        "movie", "cinema", "amc", "regal", "concert", "ticketmaster", "bar",
        "club", "bowling", "arcade", "game", "steam", "playstation", "xbox",
        "live nation", "eventbrite",
    ],
    "shopping": [
        "amazon", "target", "walmart", "best buy", "ebay", "etsy", "zara",
        "h&m", "gap", "nordstrom", "macy", "ikea", "home depot", "lowes",
        "tj maxx", "marshalls",
    ],
    "income": [
        "payroll", "direct deposit", "salary", "venmo credit", "zelle credit",
        "refund", "cashback", "interest earned", "deposit",
    ],
}


def categorize(description: str) -> str:
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(kw in desc for kw in keywords):
            return category
    return "other"


def run(csv_path: str) -> str:
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {csv_path}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

    df.columns = [c.strip().lower() for c in df.columns]

    required = {"date", "description", "amount"}
    missing = required - set(df.columns)
    if missing:
        return json.dumps({
            "error": f"CSV missing columns: {missing}. Found: {list(df.columns)}"
        })

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["category"] = df["description"].astype(str).apply(categorize)

    expenses = df[df["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()

    total_spend = expenses["amount"].sum()
    by_category = (
        expenses.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    result = {
        "total_transactions": len(df),
        "total_spend": round(total_spend, 2),
        "currency": "USD",
        "breakdown": {
            cat: {
                "total": round(amt, 2),
                "pct": round((amt / total_spend * 100) if total_spend else 0, 1),
            }
            for cat, amt in by_category.items()
        },
        "income_total": round(df[df["amount"] > 0]["amount"].sum(), 2),
    }

    return json.dumps(result, indent=2)
