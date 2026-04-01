# Recipe Book

**Live Demo:** [https://recipe-book-livid-iota.vercel.app](https://recipe-book-livid-iota.vercel.app)
A personal recipe management web app with weekly meal planning, nutrition tracking, and URL scraping built with FastAPI and a clean Jinja2 frontend.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-database-003B57?logo=sqlite&logoColor=white)

---

## Features

- **Browse & Search** — View all saved recipes and filter by category (Meals, Snacks, Desserts)
- **Add Recipes** — Manually enter recipes or scrape them directly from a URL
- **Nutrition Tracking** — Log or auto-calculate calories, protein, carbs, fat, and fiber per serving
- **Weekly Meal Planner** — Plan Breakfast, Lunch, and Dinner for every day of the week; link saved recipes or type custom meals
- **My Experience** — Mark recipes as tried and keep a personal log of notes with edit and delete support

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy |
| Database | SQLite |
| Frontend | Jinja2 templates, Alpine.js, Tailwind CSS |
| Scraping | recipe-scrapers, BeautifulSoup4 |
| Nutrition | Custom calculation via ingredient parsing |

---

## Project Structure

```
recipe-book/
├── main.py              # FastAPI app, routes, and middleware
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic request/response schemas
├── crud.py              # Database query functions
├── database.py          # DB engine and session setup
├── scraper.py           # Recipe URL scraping logic
├── nutrition_calc.py    # Nutrition calculation helpers
├── seed.py              # Sample data seeder
├── requirements.txt     # Python dependencies
├── static/
│   └── css/             # Custom CSS
└── templates/
    ├── base.html         # Shared layout
    ├── index.html        # Home page
    ├── recipes/          # Browse, detail, add, edit views
    ├── meal_plan/        # Weekly meal planner views
    └── partials/         # Reusable template components
```

---

## Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/kalibraun/recipe-book.git
cd recipe-book
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. (Optional) Seed sample data**
```bash
python seed.py
```

**5. Run the app**
```bash
uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`.

---

## API Endpoints

The app exposes a few JSON API routes used by the frontend:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scrape` | Scrape a recipe from a URL |
| `POST` | `/api/calculate-nutrition` | Calculate nutrition from ingredients |
| `GET` | `/api/recipes/search` | Search recipes by name |
| `POST` | `/api/meal-plan/slot` | Add or update a meal plan slot |
| `DELETE` | `/api/meal-plan/slot` | Clear a meal plan slot |

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.
