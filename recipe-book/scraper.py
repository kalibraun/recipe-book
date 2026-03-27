import re
import json
import requests
from typing import Optional
from bs4 import BeautifulSoup


AMOUNT_RE = re.compile(
    r'^([\d\s\u2150-\u215e\u00bc-\u00be\-\/]+\s*'
    r'(?:cups?|tbsp|tbsps?|tsp|tsps?|tablespoons?|teaspoons?|oz|ounces?|'
    r'lbs?|pounds?|grams?|g\b|kg|ml|milliliters?|liters?|l\b|'
    r'pinch(?:es)?|dash(?:es)?|cloves?|slices?|pieces?|cans?|packages?|pkgs?|'
    r'large|medium|small|whole|bunch(?:es)?|stalks?|heads?|sprigs?)?\s*)',
    re.IGNORECASE | re.UNICODE,
)


def _parse_numeric(value) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    # Strip non-numeric suffix like "320 kcal" or "8g"
    match = re.match(r'[\d\.]+', s)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _parse_servings(yields_str) -> Optional[int]:
    if not yields_str:
        return None
    match = re.search(r'\d+', str(yields_str))
    if match:
        return int(match.group())
    return None


def _parse_ingredient(raw: str) -> dict:
    raw = raw.strip()
    match = AMOUNT_RE.match(raw)
    if match and match.group(1).strip():
        amount = match.group(1).strip()
        name = raw[match.end():].strip().lstrip(',').strip()
    else:
        amount = ""
        name = raw
    return {"name": name, "amount": amount}


def _extract_from_schema(data: dict) -> dict:
    result = {"name": "", "ingredients": [], "steps": [], "servings": None, "nutrition": {}}

    result["name"] = data.get("name", "")

    # Ingredients
    raw_ings = data.get("recipeIngredient", [])
    result["ingredients"] = [_parse_ingredient(i) for i in raw_ings if i]

    # Instructions
    instructions = data.get("recipeInstructions", [])
    steps = []
    if isinstance(instructions, str):
        steps = [s.strip() for s in instructions.split("\n") if s.strip()]
    elif isinstance(instructions, list):
        for item in instructions:
            if isinstance(item, str):
                steps.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    steps.append(text.strip())
    result["steps"] = steps

    # Servings
    result["servings"] = _parse_servings(data.get("recipeYield"))

    # Nutrition
    nutrition_data = data.get("nutrition", {})
    if nutrition_data:
        result["nutrition"] = {
            "calories": _parse_numeric(nutrition_data.get("calories")),
            "protein_g": _parse_numeric(nutrition_data.get("proteinContent")),
            "carbs_g": _parse_numeric(nutrition_data.get("carbohydrateContent")),
            "fat_g": _parse_numeric(nutrition_data.get("fatContent")),
            "fiber_g": _parse_numeric(nutrition_data.get("fiberContent")),
        }

    return result


def _scrape_with_library(url: str) -> Optional[dict]:
    try:
        from recipe_scrapers import scrape_me
        scraper = scrape_me(url)

        raw_ings = scraper.ingredients()
        ingredients = [_parse_ingredient(i) for i in raw_ings if i]

        steps = []
        try:
            steps = scraper.instructions_list()
        except Exception:
            try:
                raw_steps = scraper.instructions()
                steps = [s.strip() for s in raw_steps.split("\n") if s.strip()]
            except Exception:
                pass

        nutrition = {}
        try:
            n = scraper.nutrients()
            if n:
                nutrition = {
                    "calories": _parse_numeric(n.get("calories")),
                    "protein_g": _parse_numeric(n.get("proteinContent")),
                    "carbs_g": _parse_numeric(n.get("carbohydrateContent")),
                    "fat_g": _parse_numeric(n.get("fatContent")),
                    "fiber_g": _parse_numeric(n.get("fiberContent")),
                }
        except Exception:
            pass

        name = ""
        try:
            name = scraper.title()
        except Exception:
            pass

        servings = None
        try:
            servings = _parse_servings(scraper.yields())
        except Exception:
            pass

        return {
            "name": name,
            "ingredients": ingredients,
            "steps": steps,
            "servings": servings,
            "nutrition": nutrition,
        }

    except Exception:
        return None


def _scrape_with_bs4(url: str) -> Optional[dict]:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, timeout=12, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                raw = script.string
                if not raw:
                    continue
                data = json.loads(raw)

                # Handle @graph arrays
                if isinstance(data, dict) and "@graph" in data:
                    for item in data["@graph"]:
                        if isinstance(item, dict) and "Recipe" in str(item.get("@type", "")):
                            data = item
                            break

                # Handle array at top level
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "Recipe" in str(item.get("@type", "")):
                            data = item
                            break

                if isinstance(data, dict) and "Recipe" in str(data.get("@type", "")):
                    return _extract_from_schema(data)

            except (json.JSONDecodeError, AttributeError):
                continue

    except Exception:
        pass

    return None


def scrape_recipe_url(url: str) -> dict:
    """
    Try recipe-scrapers first, fall back to BS4 schema.org parsing.
    Returns a dict with: name, ingredients, steps, servings, nutrition, missing_fields.
    """
    result = _scrape_with_library(url)
    if not result:
        result = _scrape_with_bs4(url)

    if not result:
        return {
            "success": False,
            "error": "Could not extract recipe data from this URL. Try a different site or enter details manually.",
            "data": None,
        }

    missing = []
    if not result.get("name"):
        missing.append("name")
    if not result.get("ingredients"):
        missing.append("ingredients")
    if not result.get("steps"):
        missing.append("steps")
    if not result.get("nutrition") or not any(v for v in result["nutrition"].values() if v is not None):
        missing.append("nutrition")

    return {
        "success": True,
        "partial": len(missing) > 0,
        "missing_fields": missing,
        "data": {
            "name": result.get("name", ""),
            "servings": result.get("servings"),
            "ingredients": result.get("ingredients", []),
            "steps": result.get("steps", []),
            "nutrition": result.get("nutrition", {}),
        },
    }
