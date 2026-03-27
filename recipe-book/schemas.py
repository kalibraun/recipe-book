from pydantic import BaseModel
from typing import Optional, List


class ScrapeRequest(BaseModel):
    url: str


class IngredientData(BaseModel):
    name: str
    amount: str


class NutritionCalcRequest(BaseModel):
    ingredients: List[IngredientData]
    servings: int = 1


class NutritionData(BaseModel):
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None


class ScrapedRecipe(BaseModel):
    name: str = ""
    servings: Optional[int] = None
    ingredients: List[IngredientData] = []
    steps: List[str] = []
    nutrition: NutritionData = NutritionData()


class ScrapeResponse(BaseModel):
    success: bool
    partial: bool = False
    missing_fields: List[str] = []
    error: Optional[str] = None
    data: Optional[ScrapedRecipe] = None


class SlotUpsertRequest(BaseModel):
    week_start:  str
    day_of_week: str
    meal_type:   str
    custom_name: Optional[str] = None
    recipe_id:   Optional[int] = None
