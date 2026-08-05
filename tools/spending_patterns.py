"""
tools/spending_patterns.py
---------------------------
Reads a transaction CSV and breaks spending into weekly buckets.
Identifies trending categories, large one-off purchases, and average daily spend.

Input:  csv_path (string) — same CSV format as analyze_spending
Output: JSON with weekly_breakdown, trending_categories, large_purchases,
        avg_daily_spend, busiest_week, quietest_week
"""

import json
import pandas as pd
from pathlib import Path


EXPENSE_THRESHOLD_PCT = 0.08   # flag single txn if > 8% of total spend
MIN_WEEKS_FOR_TREND   = 2      # need at least 2 weeks to call something a trend


def _categorize(description: str) -> str:
    desc = description.lower()
    rules = {
        "housing":       ["rent", "mortgage", "hoa", "utilities", "electric", "gas bill",
                          "water bill", "internet", "wifi", "comcast", "spectrum"],
        "food":          ["grocery", "groceries", "whole foods", "trader joe", "safeway",
                          "kroger", "instacart", "doordash", "uber eats", "grubhub",
                          "starbucks", "coffee", "chipotle", "mcdonald", "restaurant",
                          "dining", "pizza", "sushi"],
        "transport":     ["uber", "lyft", "taxi", "metro", "transit", "bart", "mta",
                          "gas station", "shell", "chevron", "bp", "exxon", "parking",
                          "toll", "amtrak", "greyhound"],
        "subscriptions": ["netflix", "spotify", "hulu", "disney", "apple", "amazon prime",
                          "youtube", "adobe", "notion", "slack", "zoom", "subscription"],
        "healthcare":    ["pharmacy", "walgreens", "cvs", "doctor", "hospital", "clinic",
                          "dental", "vision", "optometrist", "prescription", "rite aid"],
        "entertainment": ["movie", "cinema", "amc", "theater", "concert", "ticketmaster",
                          "stubhub", "eventbrite", "museum", "bowling", "arcade", "gym",
                          "planet fitness"],
        "shopping":      ["amazon", "target", "walmart", "costco", "best buy", "nike",
                          "zara", "h&m", "macy", "nordstrom", "gap", "uniqlo"],
    }
    for category, keywords in rules.items():
        if any(k in desc for k in keywords):
            return category
    return "other"


def run(csv_path: str) -> str:
    path = Path(csv_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {csv_path}"})

    try:
        df = pd.read_csv(path)
        df.columns = [c.strip().lower() for c in df.columns]

        for col in ("date", "description", "amount"):
            if col not in df.columns:
                return json.dumps({"error": f"Missing required column: '{col}'"})

        df["date"]   = pd.to_datetime(df["date"], errors="coerce")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df           = df.dropna(subset=["date"])
        df           = df[df["amount"] < 0].copy()   # expenses only
        df["amount"] = df["amount"].abs()
        df["category"] = df["description"].apply(_categorize)

    except Exception as e:
        return json.dumps({"error": f"Could not read CSV: {str(e)}"})

    if df.empty:
        return json.dumps({"error": "No expense transactions found in the CSV."})

    total_spend = df["amount"].sum()

    # ── Week-by-week breakdown ─────────────────────────────────────────────────
    df["week"] = df["date"].dt.to_period("W").apply(lambda p: str(p.start_time.date()))
    weekly = (
        df.groupby(["week", "category"])["amount"]
        .sum()
        .reset_index()
    )

    weekly_breakdown = {}
    for week, group in weekly.groupby("week"):
        weekly_breakdown[week] = {
            row["category"]: round(row["amount"], 2)
            for _, row in group.iterrows()
        }
        weekly_breakdown[week]["_total"] = round(group["amount"].sum(), 2)

    # ── Trending categories ────────────────────────────────────────────────────
    weeks_sorted = sorted(weekly_breakdown.keys())
    trending = []

    if len(weeks_sorted) >= MIN_WEEKS_FOR_TREND:
        first_week = weekly_breakdown[weeks_sorted[0]]
        last_week  = weekly_breakdown[weeks_sorted[-1]]

        all_cats = set(first_week.keys()) | set(last_week.keys())
        all_cats.discard("_total")

        for cat in all_cats:
            first_amt = first_week.get(cat, 0)
            last_amt  = last_week.get(cat, 0)
            if first_amt > 0 and last_amt > first_amt:
                pct_change = ((last_amt - first_amt) / first_amt) * 100
                if pct_change >= 20:
                    trending.append({
                        "category":   cat,
                        "first_week": round(first_amt, 2),
                        "last_week":  round(last_amt, 2),
                        "change_pct": round(pct_change, 1),
                        "direction":  "increasing",
                    })

    trending.sort(key=lambda x: -x["change_pct"])

    # ── Large one-off purchases ────────────────────────────────────────────────
    threshold = total_spend * EXPENSE_THRESHOLD_PCT
    large = df[df["amount"] >= threshold].copy()
    large_purchases = [
        {
            "date":        str(row["date"].date()),
            "description": row["description"],
            "amount":      round(row["amount"], 2),
            "category":    row["category"],
            "pct_of_spend": round(row["amount"] / total_spend * 100, 1),
        }
        for _, row in large.sort_values("amount", ascending=False).iterrows()
    ]

    # ── Avg daily spend ────────────────────────────────────────────────────────
    date_range = (df["date"].max() - df["date"].min()).days + 1
    avg_daily  = round(total_spend / date_range, 2) if date_range > 0 else 0

    # ── Busiest / quietest week ───────────────────────────────────────────────
    week_totals = {w: d["_total"] for w, d in weekly_breakdown.items()}
    busiest  = max(week_totals, key=week_totals.get) if week_totals else None
    quietest = min(week_totals, key=week_totals.get) if week_totals else None

    result = {
        "total_spend":       round(total_spend, 2),
        "avg_daily_spend":   avg_daily,
        "date_range_days":   date_range,
        "weekly_breakdown":  weekly_breakdown,
        "trending_categories": trending if trending else "Not enough weeks of data to detect trends.",
        "large_purchases":   large_purchases,
        "busiest_week":      {"week": busiest,  "total": week_totals.get(busiest)},
        "quietest_week":     {"week": quietest, "total": week_totals.get(quietest)},
    }

    return json.dumps(result, indent=2)
