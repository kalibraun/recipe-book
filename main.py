from typing import Optional, List
from datetime import date, timedelta
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

import crud
import models
from database import engine, get_db
from schemas import ScrapeRequest, NutritionCalcRequest, SlotUpsertRequest
from scraper import scrape_recipe_url
from nutrition_calc import calculate_recipe_nutrition

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Recipe Book")
app.add_middleware(SessionMiddleware, secret_key="recipe-book-secret-key-change-me")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def _human_week(week_start: str) -> str:
    start = date.fromisoformat(week_start)
    end   = start + timedelta(days=6)
    if start.year == end.year:
        return f"{start.strftime('%b %-d')} – {end.strftime('%b %-d, %Y')}"
    return f"{start.strftime('%b %-d, %Y')} – {end.strftime('%b %-d, %Y')}"


def _day_date(week_start: str, offset: int) -> str:
    d = date.fromisoformat(week_start) + timedelta(days=offset)
    return d.strftime('%b %-d')


def _format_note_date(dt) -> str:
    return dt.strftime('%b %-d, %Y') if dt else ''

templates.env.filters["human_week"]     = _human_week
templates.env.filters["day_date"]       = _day_date
templates.env.filters["format_note_date"] = _format_note_date


# ── Flash helpers ──────────────────────────────────────────────────────────────

def flash(request: Request, message: str, category: str = "success"):
    request.session.setdefault("_flashes", []).append({"message": message, "category": category})


def get_flashes(request: Request):
    messages = request.session.pop("_flashes", [])
    return messages


# ── Home ───────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    recent = crud.get_recent_recipes(db, limit=6)
    counts = crud.get_category_counts(db)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_recipes": recent,
        "category_counts": counts,
        "flashes": get_flashes(request),
    })


# ── Browse ─────────────────────────────────────────────────────────────────────

@app.get("/recipes", response_class=HTMLResponse)
async def browse_recipes(
    request: Request,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    recipes = crud.get_recipes(db, category=category)
    return templates.TemplateResponse("recipes/browse.html", {
        "request": request,
        "recipes": recipes,
        "active_category": category,
        "flashes": get_flashes(request),
    })


# ── Detail ─────────────────────────────────────────────────────────────────────

@app.get("/recipes/add", response_class=HTMLResponse)
async def add_recipe_form(request: Request):
    return templates.TemplateResponse("recipes/add.html", {
        "request": request,
        "flashes": get_flashes(request),
    })


@app.get("/recipes/{recipe_id}", response_class=HTMLResponse)
async def recipe_detail(request: Request, recipe_id: int, db: Session = Depends(get_db)):
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return templates.TemplateResponse("recipes/detail.html", {
        "request": request,
        "recipe": recipe,
        "flashes": get_flashes(request),
    })


# ── Create ─────────────────────────────────────────────────────────────────────

@app.post("/recipes/add")
async def create_recipe(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    source_url: Optional[str] = Form(None),
    servings: int = Form(...),
    steps: str = Form(...),
    notes: Optional[str] = Form(None),
    ingredient_names: List[str] = Form(default=[]),
    ingredient_amounts: List[str] = Form(default=[]),
    calories: Optional[str] = Form(None),
    protein_g: Optional[str] = Form(None),
    carbs_g: Optional[str] = Form(None),
    fat_g: Optional[str] = Form(None),
    fiber_g: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    def to_float(v):
        try:
            return float(v) if v and v.strip() else None
        except (ValueError, AttributeError):
            return None

    recipe = crud.create_recipe(
        db=db,
        name=name,
        category=category,
        servings=servings,
        steps=steps,
        ingredient_names=ingredient_names,
        ingredient_amounts=ingredient_amounts,
        source_url=source_url.strip() if source_url and source_url.strip() else None,
        notes=notes,
        calories=to_float(calories),
        protein_g=to_float(protein_g),
        carbs_g=to_float(carbs_g),
        fat_g=to_float(fat_g),
        fiber_g=to_float(fiber_g),
    )
    flash(request, f'"{recipe.name}" has been added to your recipe book.')
    return RedirectResponse(f"/recipes/{recipe.id}", status_code=303)


# ── Edit ───────────────────────────────────────────────────────────────────────

@app.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
async def edit_recipe_form(request: Request, recipe_id: int, db: Session = Depends(get_db)):
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return templates.TemplateResponse("recipes/edit.html", {
        "request": request,
        "recipe": recipe,
        "flashes": get_flashes(request),
    })


@app.post("/recipes/{recipe_id}/edit")
async def update_recipe(
    request: Request,
    recipe_id: int,
    name: str = Form(...),
    category: str = Form(...),
    source_url: Optional[str] = Form(None),
    servings: int = Form(...),
    steps: str = Form(...),
    notes: Optional[str] = Form(None),
    ingredient_names: List[str] = Form(default=[]),
    ingredient_amounts: List[str] = Form(default=[]),
    calories: Optional[str] = Form(None),
    protein_g: Optional[str] = Form(None),
    carbs_g: Optional[str] = Form(None),
    fat_g: Optional[str] = Form(None),
    fiber_g: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    def to_float(v):
        try:
            return float(v) if v and v.strip() else None
        except (ValueError, AttributeError):
            return None

    recipe = crud.update_recipe(
        db=db,
        recipe_id=recipe_id,
        name=name,
        category=category,
        servings=servings,
        steps=steps,
        ingredient_names=ingredient_names,
        ingredient_amounts=ingredient_amounts,
        source_url=source_url.strip() if source_url and source_url.strip() else None,
        notes=notes,
        calories=to_float(calories),
        protein_g=to_float(protein_g),
        carbs_g=to_float(carbs_g),
        fat_g=to_float(fat_g),
        fiber_g=to_float(fiber_g),
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    flash(request, f'"{recipe.name}" has been updated.')
    return RedirectResponse(f"/recipes/{recipe.id}", status_code=303)


# ── Personal data ──────────────────────────────────────────────────────────────

@app.post("/recipes/{recipe_id}/personal")
async def update_personal(
    request: Request,
    recipe_id: int,
    tried: Optional[str] = Form(None),
    personal_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    recipe = crud.update_personal(
        db=db,
        recipe_id=recipe_id,
        tried=tried == "on",
        personal_notes=personal_notes,
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RedirectResponse(f"/recipes/{recipe_id}#personal", status_code=303)


# ── Delete ─────────────────────────────────────────────────────────────────────

@app.post("/recipes/{recipe_id}/delete")
async def delete_recipe(request: Request, recipe_id: int, db: Session = Depends(get_db)):
    recipe = crud.get_recipe(db, recipe_id)
    name = recipe.name if recipe else "Recipe"
    crud.delete_recipe(db, recipe_id)
    flash(request, f'"{name}" has been deleted.', category="info")
    return RedirectResponse("/recipes", status_code=303)


# ── Recipe Notes ──────────────────────────────────────────────────────────────

@app.post("/recipes/{recipe_id}/notes")
async def create_note(
    request: Request,
    recipe_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    content = content.strip()
    if content:
        crud.create_recipe_note(db, recipe_id, content)
    return RedirectResponse(f"/recipes/{recipe_id}#personal", status_code=303)


@app.post("/recipes/{recipe_id}/notes/{note_id}/edit")
async def edit_note(
    request: Request,
    recipe_id: int,
    note_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    content = content.strip()
    if content:
        crud.update_recipe_note(db, note_id, content)
    return RedirectResponse(f"/recipes/{recipe_id}#personal", status_code=303)


@app.post("/recipes/{recipe_id}/notes/{note_id}/delete")
async def delete_note(
    request: Request,
    recipe_id: int,
    note_id: int,
    db: Session = Depends(get_db),
):
    crud.delete_recipe_note(db, note_id)
    return RedirectResponse(f"/recipes/{recipe_id}#personal", status_code=303)


# ── Meal Plan helpers ─────────────────────────────────────────────────────────

def current_week_start() -> str:
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


def week_start_for(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
        return (d - timedelta(days=d.weekday())).isoformat()
    except ValueError:
        return current_week_start()


# ── Scrape API ─────────────────────────────────────────────────────────────────

@app.post("/api/scrape")
async def scrape_url(payload: ScrapeRequest):
    result = scrape_recipe_url(payload.url)
    return JSONResponse(content=result)


@app.post("/api/calculate-nutrition")
async def calc_nutrition(payload: NutritionCalcRequest):
    result = calculate_recipe_nutrition(
        ingredients=[i.dict() for i in payload.ingredients],
        servings=payload.servings,
    )
    return JSONResponse(content=result)


# ── Meal Plan ──────────────────────────────────────────────────────────────────

@app.get("/meal-plan", response_class=HTMLResponse)
async def meal_plan_page(
    request: Request,
    week: Optional[str] = None,
    db: Session = Depends(get_db),
):
    ws = week_start_for(week) if week else current_week_start()
    plan = crud.get_or_create_meal_plan(db, ws)
    slots_map = {(s.day_of_week.value, s.meal_type.value): s for s in plan.slots}
    ws_date = date.fromisoformat(ws)
    return templates.TemplateResponse("meal_plan/index.html", {
        "request":   request,
        "flashes":   get_flashes(request),
        "plan":      plan,
        "week_start": ws,
        "prev_week": (ws_date - timedelta(weeks=1)).isoformat(),
        "next_week": (ws_date + timedelta(weeks=1)).isoformat(),
        "slots_map": slots_map,
        "days":  ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "meals": ["breakfast", "lunch", "dinner"],
    })


@app.post("/api/meal-plan/slot")
async def api_upsert_slot(payload: SlotUpsertRequest, db: Session = Depends(get_db)):
    plan = crud.get_or_create_meal_plan(db, payload.week_start)
    slot = crud.upsert_meal_slot(
        db=db,
        meal_plan_id=plan.id,
        day_of_week=payload.day_of_week,
        meal_type=payload.meal_type,
        custom_name=payload.custom_name,
        recipe_id=payload.recipe_id,
    )
    return JSONResponse({"ok": True, "slot": {
        "id":          slot.id,
        "day_of_week": slot.day_of_week.value,
        "meal_type":   slot.meal_type.value,
        "custom_name": slot.custom_name,
        "recipe_id":   slot.recipe_id,
        "recipe_name": slot.recipe.name if slot.recipe else None,
    }})


@app.delete("/api/meal-plan/slot")
async def api_clear_slot(
    week_start:  str,
    day_of_week: str,
    meal_type:   str,
    db: Session = Depends(get_db),
):
    plan = crud.get_meal_plan(db, week_start)
    if plan:
        crud.clear_meal_slot(db, plan.id, day_of_week, meal_type)
    return JSONResponse({"ok": True})


@app.get("/api/recipes/search")
async def api_search_recipes(q: str = "", db: Session = Depends(get_db)):
    if not q.strip():
        return JSONResponse([])
    results = crud.search_recipes(db, q.strip())
    return JSONResponse([
        {"id": r.id, "name": r.name, "category": r.category.value}
        for r in results
    ])
