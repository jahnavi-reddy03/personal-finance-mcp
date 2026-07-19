"""
tools/tips.py
--------------
Returns 3-5 personalized savings tips for a given spending category.
Uses GPT-3.5-turbo so the advice stays practical and fresh.
Falls back to a curated static list if no API key is set.
"""

import json
from typing import Optional


# ── Static fallback tips ──────────────────────────────────────────────────────
STATIC_TIPS: dict[str, list[str]] = {
    "food": [
        "Meal-prep on Sundays — cooking in bulk cuts per-meal cost by ~40%.",
        "Use the 'weekly specials' section in your grocery app before making a list.",
        "Cancel one delivery app and default to pickup for a month; fees add up fast.",
        "Try a no-restaurant week once a month — treat it as a challenge, not a punishment.",
        "Keep a running list of cheap meals you actually enjoy so you don't default to delivery when tired.",
    ],
    "transport": [
        "If you Uber more than 3x a week, a monthly transit pass almost always wins on price.",
        "Combine errands into one trip — sounds obvious, but mapping it out saves real gas money.",
        "Check if your employer offers pre-tax commuter benefits; it's free money most people miss.",
        "For short rides, bike-share or e-scooter rentals are usually cheaper than Uber Pool.",
        "Carpool apps like Waze Carpool can cut commute costs roughly in half.",
    ],
    "subscriptions": [
        "Do a 10-minute subscription audit right now — list every recurring charge and cancel anything you haven't used in 30 days.",
        "Share streaming plans with a family member or trusted friend; most allow 2-4 profiles.",
        "Use a service like Trim or Rocket Money to auto-detect and cancel forgotten subscriptions.",
        "Switch annual billing where you use something consistently — usually 15-20% cheaper.",
        "Pause instead of cancel when you're busy — Netflix, Hulu, and most others allow it.",
    ],
    "housing": [
        "Negotiate your rent at renewal — landlords hate vacancies; even 2-3% off is worth asking.",
        "Check if you qualify for any utility assistance programs; many states have them.",
        "Lower your thermostat by 2°F and use a smart plug for high-draw devices — cuts electric bills noticeably.",
        "Refinance if rates dropped since you locked in your mortgage.",
        "Rent out a parking spot or storage space if you have one — passive income from existing assets.",
    ],
    "entertainment": [
        "Look up free local events — most cities have weekly listings most people never check.",
        "Use your library card: free e-books, audiobooks, and even museum passes in many cities.",
        "Happy hour is underrated — same vibe, 30-50% cheaper.",
        "Buy concert/event tickets on the secondary market closer to the date; prices usually drop.",
        "Rotate which streaming service you keep active instead of running all of them at once.",
    ],
    "shopping": [
        "Wait 48 hours before buying anything over $50 — impulse drops dramatically.",
        "Use browser extensions like Honey or Capital One Shopping to auto-apply coupons.",
        "Buy secondhand first — ThredUp, Poshmark, and Facebook Marketplace for clothes and furniture.",
        "Unsubscribe from brand emails; promotional emails are engineered to make you spend.",
        "Track price history on CamelCamelCamel before buying anything on Amazon.",
    ],
    "healthcare": [
        "Use GoodRx or Mark Cuban's Cost Plus Drugs — can cut prescription costs by 80%+.",
        "Schedule preventive care before your deductible resets; it's usually free.",
        "Check if your employer's EAP covers free therapy sessions — many do and employees don't know.",
        "Generic drugs are FDA-equivalent to brand names and cost a fraction of the price.",
        "Ask for an itemized hospital bill and dispute any errors — billing mistakes are extremely common.",
    ],
    "other": [
        "Track every transaction for one week — awareness alone changes spending behavior.",
        "Automate a fixed savings transfer on payday so the money is gone before you can spend it.",
        "Set a weekly 'fun money' cash limit — once it's gone, it's gone.",
        "Review your spending with this tool monthly so small creep doesn't become a big problem.",
    ],
}


def run(category: str, api_key: Optional[str] = None) -> str:
    category = category.lower().strip()

    if api_key:
        try:
            return _gpt_tips(category, api_key)
        except Exception as e:
            # Graceful fallback — log error but don't surface it to the user
            pass

    tips = STATIC_TIPS.get(category, STATIC_TIPS["other"])
    return json.dumps({"category": category, "tips": tips}, indent=2)


def _gpt_tips(category: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    prompt = (
        f"Give me exactly 5 specific, actionable money-saving tips for the "
        f"'{category}' spending category. "
        f"Keep each tip to 1-2 sentences. Be practical, not generic. "
        f"Return a JSON object with a single key 'tips' containing a list of strings."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a practical personal finance coach. "
                    "Give real, specific advice — not platitudes. "
                    "Always respond with valid JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)
    parsed["category"] = category
    return json.dumps(parsed, indent=2)
