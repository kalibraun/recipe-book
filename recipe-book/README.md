# My Recipe Book

A personal recipe management app with weekly meal planning.

## Features

- **Browse & Search** — View all saved recipes, filter by category (Meals, Snacks, Desserts)
- **Add Recipes** — Manually enter recipes or scrape them directly from a URL
- **Nutrition Tracking** — Log or auto-calculate calories, protein, carbs, fat, and fiber per serving
- **Weekly Meal Planner** — Plan Breakfast, Lunch, and Dinner for every day of the week; link saved recipes or type custom meals
- **My Experience** — Mark recipes as tried and keep a personal log of notes with edit and delete support

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** Jinja2 templates, Alpine.js, Tailwind CSS

## Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/kalibraun/recipe-book.git
cd recipe-book/recipe-book
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the app**
```bash
uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`.
