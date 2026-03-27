from typing import Optional, List
from sqlalchemy.orm import Session
from models import Recipe, Ingredient, Nutrition, CategoryEnum, RecipeNote, MealPlan, MealSlot, DayOfWeekEnum, MealTypeEnum


def get_recipes(db: Session, category: Optional[str] = None) -> List[Recipe]:
    q = db.query(Recipe)
    if category:
        try:
            cat = CategoryEnum(category)
            q = q.filter(Recipe.category == cat)
        except ValueError:
            pass
    return q.order_by(Recipe.created_at.desc()).all()


def get_recipe(db: Session, recipe_id: int) -> Optional[Recipe]:
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def get_recent_recipes(db: Session, limit: int = 6) -> List[Recipe]:
    return db.query(Recipe).order_by(Recipe.created_at.desc()).limit(limit).all()


def get_category_counts(db: Session) -> dict:
    counts = {}
    for cat in CategoryEnum:
        counts[cat.value] = db.query(Recipe).filter(Recipe.category == cat).count()
    return counts


def create_recipe(
    db: Session,
    name: str,
    category: str,
    servings: int,
    steps: str,
    ingredient_names: List[str],
    ingredient_amounts: List[str],
    source_url: Optional[str] = None,
    notes: Optional[str] = None,
    calories: Optional[float] = None,
    protein_g: Optional[float] = None,
    carbs_g: Optional[float] = None,
    fat_g: Optional[float] = None,
    fiber_g: Optional[float] = None,
) -> Recipe:
    recipe = Recipe(
        name=name,
        category=CategoryEnum(category),
        source_url=source_url or None,
        servings=servings,
        steps=steps,
        notes=notes or None,
    )
    db.add(recipe)
    db.flush()

    for i, (ing_name, ing_amount) in enumerate(zip(ingredient_names, ingredient_amounts)):
        if ing_name.strip():
            db.add(Ingredient(
                recipe_id=recipe.id,
                name=ing_name.strip(),
                amount=ing_amount.strip(),
                sort_order=i,
            ))

    has_nutrition = any(v is not None for v in [calories, protein_g, carbs_g, fat_g, fiber_g])
    if has_nutrition:
        db.add(Nutrition(
            recipe_id=recipe.id,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
        ))

    db.commit()
    db.refresh(recipe)
    return recipe


def update_recipe(
    db: Session,
    recipe_id: int,
    name: str,
    category: str,
    servings: int,
    steps: str,
    ingredient_names: List[str],
    ingredient_amounts: List[str],
    source_url: Optional[str] = None,
    notes: Optional[str] = None,
    calories: Optional[float] = None,
    protein_g: Optional[float] = None,
    carbs_g: Optional[float] = None,
    fat_g: Optional[float] = None,
    fiber_g: Optional[float] = None,
) -> Optional[Recipe]:
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return None

    recipe.name = name
    recipe.category = CategoryEnum(category)
    recipe.source_url = source_url or None
    recipe.servings = servings
    recipe.steps = steps
    recipe.notes = notes or None

    # Delete and reinsert ingredients
    for ing in recipe.ingredients:
        db.delete(ing)
    db.flush()

    for i, (ing_name, ing_amount) in enumerate(zip(ingredient_names, ingredient_amounts)):
        if ing_name.strip():
            db.add(Ingredient(
                recipe_id=recipe.id,
                name=ing_name.strip(),
                amount=ing_amount.strip(),
                sort_order=i,
            ))

    # Delete and reinsert nutrition
    if recipe.nutrition:
        db.delete(recipe.nutrition)
        db.flush()

    has_nutrition = any(v is not None for v in [calories, protein_g, carbs_g, fat_g, fiber_g])
    if has_nutrition:
        db.add(Nutrition(
            recipe_id=recipe.id,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
        ))

    db.commit()
    db.refresh(recipe)
    return recipe


def update_personal(
    db: Session,
    recipe_id: int,
    tried: bool,
    personal_notes: Optional[str],
) -> Optional[Recipe]:
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return None
    recipe.tried = tried
    recipe.personal_notes = personal_notes or None
    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: int) -> bool:
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return False
    db.delete(recipe)
    db.commit()
    return True


# ── Recipe Notes ──────────────────────────────────────────────────────────────

def create_recipe_note(db: Session, recipe_id: int, content: str) -> RecipeNote:
    note = RecipeNote(recipe_id=recipe_id, content=content.strip())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_recipe_note(db: Session, note_id: int, content: str) -> Optional[RecipeNote]:
    note = db.query(RecipeNote).filter(RecipeNote.id == note_id).first()
    if not note:
        return None
    note.content = content.strip()
    db.commit()
    db.refresh(note)
    return note


def delete_recipe_note(db: Session, note_id: int) -> bool:
    note = db.query(RecipeNote).filter(RecipeNote.id == note_id).first()
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


# ── Meal Plan ─────────────────────────────────────────────────────────────────

def get_or_create_meal_plan(db: Session, week_start: str) -> MealPlan:
    plan = db.query(MealPlan).filter(MealPlan.week_start == week_start).first()
    if not plan:
        plan = MealPlan(week_start=week_start)
        db.add(plan)
        db.commit()
        db.refresh(plan)
    return plan


def get_meal_plan(db: Session, week_start: str) -> Optional[MealPlan]:
    return db.query(MealPlan).filter(MealPlan.week_start == week_start).first()


def upsert_meal_slot(
    db: Session,
    meal_plan_id: int,
    day_of_week: str,
    meal_type: str,
    custom_name: Optional[str] = None,
    recipe_id: Optional[int] = None,
) -> MealSlot:
    slot = (
        db.query(MealSlot)
        .filter(
            MealSlot.meal_plan_id == meal_plan_id,
            MealSlot.day_of_week == DayOfWeekEnum(day_of_week),
            MealSlot.meal_type == MealTypeEnum(meal_type),
        )
        .first()
    )
    if not slot:
        slot = MealSlot(
            meal_plan_id=meal_plan_id,
            day_of_week=DayOfWeekEnum(day_of_week),
            meal_type=MealTypeEnum(meal_type),
        )
        db.add(slot)
    if recipe_id:
        slot.recipe_id = recipe_id
        slot.custom_name = None
    else:
        slot.custom_name = custom_name or None
        slot.recipe_id = None
    db.commit()
    db.refresh(slot)
    return slot


def clear_meal_slot(
    db: Session,
    meal_plan_id: int,
    day_of_week: str,
    meal_type: str,
) -> bool:
    slot = (
        db.query(MealSlot)
        .filter(
            MealSlot.meal_plan_id == meal_plan_id,
            MealSlot.day_of_week == DayOfWeekEnum(day_of_week),
            MealSlot.meal_type == MealTypeEnum(meal_type),
        )
        .first()
    )
    if not slot:
        return False
    db.delete(slot)
    db.commit()
    return True


def search_recipes(db: Session, q: str, limit: int = 10) -> List[Recipe]:
    return (
        db.query(Recipe)
        .filter(Recipe.name.ilike(f"%{q}%"))
        .order_by(Recipe.name)
        .limit(limit)
        .all()
    )
