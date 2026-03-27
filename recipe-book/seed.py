"""
Run: python seed.py
Inserts 3 sample recipes for testing the UI.
"""
from database import SessionLocal, engine
import models
from models import Base

Base.metadata.create_all(bind=engine)

RECIPES = [
    {
        "name": "Lemon Herb Roast Chicken",
        "category": models.CategoryEnum.meals,
        "source_url": None,
        "servings": 4,
        "steps": (
            "Preheat your oven to 425°F (220°C).\n"
            "Pat the chicken dry with paper towels and place in a roasting pan.\n"
            "Zest and juice one lemon. Mix with 3 tbsp softened butter, 2 minced garlic cloves, "
            "1 tsp thyme, and 1 tsp rosemary.\n"
            "Rub the herb butter all over the chicken, including under the skin of the breast.\n"
            "Season generously with salt and pepper inside and out. Place lemon halves inside the cavity.\n"
            "Roast for 60–75 minutes, until juices run clear and a thermometer reads 165°F at the thigh.\n"
            "Rest for 10 minutes before carving."
        ),
        "notes": "For extra-crispy skin, refrigerate the chicken uncovered for 1–2 hours before roasting.",
        "ingredients": [
            ("1 whole chicken (about 4 lbs)", ""),
            ("3 tbsp", "unsalted butter, softened"),
            ("1", "lemon, zested and halved"),
            ("2 cloves", "garlic, minced"),
            ("1 tsp", "fresh thyme leaves"),
            ("1 tsp", "fresh rosemary, chopped"),
            ("to taste", "salt and black pepper"),
        ],
        "nutrition": {"calories": 420, "protein_g": 48, "carbs_g": 2, "fat_g": 24, "fiber_g": 0},
    },
    {
        "name": "Avocado Toast with Everything Bagel Seasoning",
        "category": models.CategoryEnum.snacks,
        "source_url": None,
        "servings": 2,
        "steps": (
            "Toast the sourdough slices to your preferred doneness.\n"
            "Halve the avocados and remove the pits. Scoop the flesh into a bowl.\n"
            "Add lemon juice, a pinch of red pepper flakes, and season with salt. Mash gently with a fork "
            "— leave some texture.\n"
            "Spread the avocado mixture generously over the toast.\n"
            "Sprinkle everything bagel seasoning over the top.\n"
            "Optionally, top with a soft-boiled egg, cherry tomatoes, or microgreens."
        ),
        "notes": "Best eaten immediately before the avocado oxidises.",
        "ingredients": [
            ("2 slices", "sourdough bread"),
            ("2 ripe", "avocados"),
            ("1 tbsp", "lemon juice"),
            ("1 tsp", "everything bagel seasoning"),
            ("pinch", "red pepper flakes"),
            ("to taste", "salt"),
        ],
        "nutrition": {"calories": 340, "protein_g": 7, "carbs_g": 32, "fat_g": 22, "fiber_g": 10},
    },
    {
        "name": "Classic Chocolate Chip Cookies",
        "category": models.CategoryEnum.desserts,
        "source_url": None,
        "servings": 24,
        "steps": (
            "Preheat oven to 375°F (190°C). Line two baking sheets with parchment paper.\n"
            "Whisk together flour, baking soda, and salt in a bowl. Set aside.\n"
            "Beat butter and both sugars together with a mixer on medium until light and fluffy, about 3 minutes.\n"
            "Add the eggs one at a time, then mix in the vanilla.\n"
            "Reduce mixer speed to low and gradually add the flour mixture until just combined.\n"
            "Fold in the chocolate chips with a spatula.\n"
            "Drop rounded tablespoons of dough onto prepared baking sheets, spacing 2 inches apart.\n"
            "Bake for 9–11 minutes until edges are golden but centres still look slightly underdone.\n"
            "Cool on the baking sheet for 5 minutes, then transfer to a wire rack."
        ),
        "notes": "Chill the dough for 24–72 hours in the refrigerator for deeper, more complex flavour and thicker cookies.",
        "ingredients": [
            ("2 1/4 cups", "all-purpose flour"),
            ("1 tsp", "baking soda"),
            ("1 tsp", "salt"),
            ("1 cup (2 sticks)", "unsalted butter, room temperature"),
            ("3/4 cup", "granulated sugar"),
            ("3/4 cup", "packed brown sugar"),
            ("2 large", "eggs"),
            ("2 tsp", "vanilla extract"),
            ("2 cups", "semi-sweet chocolate chips"),
        ],
        "nutrition": {"calories": 185, "protein_g": 2, "carbs_g": 26, "fat_g": 9, "fiber_g": 1},
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(models.Recipe).count()
        if existing > 0:
            print(f"Database already has {existing} recipe(s). Skipping seed.")
            return

        for data in RECIPES:
            recipe = models.Recipe(
                name=data["name"],
                category=data["category"],
                source_url=data.get("source_url"),
                servings=data["servings"],
                steps=data["steps"],
                notes=data.get("notes"),
            )
            db.add(recipe)
            db.flush()

            for i, (amount, name) in enumerate(data["ingredients"]):
                # Handle both (amount, name) and (name, "") formats
                if name:
                    ing_name, ing_amount = name, amount
                else:
                    ing_name, ing_amount = amount, ""
                db.add(models.Ingredient(
                    recipe_id=recipe.id,
                    name=ing_name,
                    amount=ing_amount,
                    sort_order=i,
                ))

            n = data.get("nutrition", {})
            if n:
                db.add(models.Nutrition(
                    recipe_id=recipe.id,
                    **n,
                ))

        db.commit()
        print(f"Seeded {len(RECIPES)} recipes successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
