import os
import re
import requests
from typing import Optional

USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Approximate grams per common unit
UNIT_GRAMS: dict[str, float] = {
    "cup": 240, "cups": 240,
    "tbsp": 15, "tablespoon": 15, "tablespoons": 15, "tbs": 15,
    "tsp": 5, "teaspoon": 5, "teaspoons": 5,
    "oz": 28.35, "ounce": 28.35, "ounces": 28.35,
    "lb": 453.6, "lbs": 453.6, "pound": 453.6, "pounds": 453.6,
    "g": 1, "gram": 1, "grams": 1,
    "kg": 1000, "kilogram": 1000,
    "ml": 1, "milliliter": 1, "milliliters": 1,
    "l": 1000, "liter": 1000, "liters": 1000,
    "clove": 5, "cloves": 5,
    "slice": 30, "slices": 30,
    "can": 400, "cans": 400,
    "stalk": 40, "stalks": 40,
    "sprig": 5, "sprigs": 5,
    "head": 500,
    "pinch": 0.5,
    "dash": 0.5,
    "handful": 30,
    "large": 120, "medium": 80, "small": 50,
    "whole": 100, "piece": 100, "pieces": 100,
}

# USDA nutrient IDs
NUTRIENT_IDS = {
    "calories": 1008,
    "protein_g": 1003,
    "carbs_g": 1005,
    "fat_g": 1004,
    "fiber_g": 1079,
}


def parse_quantity_grams(amount_str: str) -> float:
    """Parse an amount string like '2 cups', '1/2 tbsp', '1 1/2 oz' to approximate grams."""
    if not amount_str:
        return 100.0

    s = re.sub(r'\(.*?\)', '', amount_str.lower()).strip()

    # Extract number: mixed fraction (1 1/2), simple fraction (1/2), or decimal
    num_match = re.match(r'(\d+)\s+(\d+)/(\d+)|(\d+)/(\d+)|(\d+\.?\d*)', s)
    quantity = 1.0
    if num_match:
        if num_match.group(1):  # mixed fraction
            quantity = int(num_match.group(1)) + int(num_match.group(2)) / int(num_match.group(3))
        elif num_match.group(4):  # simple fraction
            quantity = int(num_match.group(4)) / int(num_match.group(5))
        elif num_match.group(6):  # decimal/integer
            quantity = float(num_match.group(6))

    # Find first matching unit word
    for word in re.findall(r'[a-zA-Z]+', s):
        if word in UNIT_GRAMS:
            return quantity * UNIT_GRAMS[word]

    # No recognised unit — treat as countable items (~100g each)
    return quantity * 100.0


def lookup_ingredient(name: str, api_key: str = USDA_API_KEY) -> Optional[dict]:
    """Return nutrition per 100g for the best USDA match, or None on failure."""
    try:
        resp = requests.get(
            USDA_SEARCH_URL,
            params={
                "query": name,
                "dataType": "SR Legacy,Foundation",
                "pageSize": 1,
                "api_key": api_key,
            },
            timeout=6,
        )
        resp.raise_for_status()
        foods = resp.json().get("foods", [])
        if not foods:
            return None

        nutrients = {n["nutrientId"]: n.get("value") or 0
                     for n in foods[0].get("foodNutrients", [])}
        return {key: nutrients.get(nid, 0) for key, nid in NUTRIENT_IDS.items()}
    except Exception:
        return None


def calculate_recipe_nutrition(ingredients: list[dict], servings: int) -> dict:
    """
    Calculate per-serving nutrition from a list of {name, amount} dicts.
    Returns {per_serving: {...}, found: int, total: int, missing: [str]}.
    """
    totals = {k: 0.0 for k in NUTRIENT_IDS}
    found, missing = 0, []

    for ing in ingredients:
        name = (ing.get("name") or "").strip()
        if not name:
            continue
        grams = parse_quantity_grams(ing.get("amount") or "")
        per_100g = lookup_ingredient(name)
        if per_100g:
            factor = grams / 100.0
            for k in totals:
                totals[k] += per_100g[k] * factor
            found += 1
        else:
            missing.append(name)

    divisor = max(servings, 1)
    per_serving = {k: round(v / divisor, 1) for k, v in totals.items()}

    return {
        "per_serving": per_serving,
        "found": found,
        "total": found + len(missing),
        "missing": missing,
    }
