import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from database import Base


class CategoryEnum(str, enum.Enum):
    meals = "Meals"
    snacks = "Snacks"
    desserts = "Desserts"


class DayOfWeekEnum(str, enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class MealTypeEnum(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(SAEnum(CategoryEnum), nullable=False)
    source_url = Column(String(2048), nullable=True)
    servings = Column(Integer, nullable=False, default=4)
    steps = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    tried = Column(Boolean, nullable=False, default=False)
    personal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ingredients = relationship(
        "Ingredient", back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="Ingredient.sort_order",
    )
    nutrition = relationship(
        "Nutrition", back_populates="recipe",
        uselist=False,
        cascade="all, delete-orphan",
    )
    experience_notes = relationship(
        "RecipeNote", back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeNote.created_at.desc()",
    )

    @property
    def source_label(self):
        return self.source_url if self.source_url else "Original"

    @property
    def source_domain(self):
        if not self.source_url:
            return None
        from urllib.parse import urlparse
        try:
            return urlparse(self.source_url).netloc.replace("www.", "")
        except Exception:
            return self.source_url


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    name = Column(String(255), nullable=False)
    amount = Column(String(100), nullable=False, default="")
    sort_order = Column(Integer, default=0)

    recipe = relationship("Recipe", back_populates="ingredients")


class Nutrition(Base):
    __tablename__ = "nutrition"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, unique=True)
    calories = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)

    recipe = relationship("Recipe", back_populates="nutrition")


class RecipeNote(Base):
    __tablename__ = "recipe_notes"

    id         = Column(Integer, primary_key=True, index=True)
    recipe_id  = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recipe = relationship("Recipe", back_populates="experience_notes")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id         = Column(Integer, primary_key=True, index=True)
    week_start = Column(String(10), nullable=False, unique=True)  # ISO date "YYYY-MM-DD" (always a Monday)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    slots = relationship("MealSlot", back_populates="meal_plan", cascade="all, delete-orphan")


class MealSlot(Base):
    __tablename__ = "meal_slots"

    id           = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    day_of_week  = Column(SAEnum(DayOfWeekEnum), nullable=False)
    meal_type    = Column(SAEnum(MealTypeEnum), nullable=False)
    custom_name  = Column(String(255), nullable=True)
    recipe_id    = Column(Integer, ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)

    meal_plan = relationship("MealPlan", back_populates="slots")
    recipe    = relationship("Recipe")
