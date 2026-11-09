# NutriAI — AI-Assisted Diet Recommendation Website

A complete Flask + HTML/CSS/JavaScript project using the supplied **NutriAI_Final_Dataset(Food Catalog).csv**.

## What is included

- Clean responsive NutriAI web UI
- Adult user profile form
- AI-assisted 7-day meal recommendation engine
- Variety-first selection to reduce repeated dishes
- Breakfast, lunch, snack and dinner slots
- Diet preference filtering
- Goal/activity-aware estimated daily energy target
- Swap-meal feature
- Food catalog search
- Recipe/ingredient modal
- Automatic grocery list from selected ingredients
- Browser localStorage for profile and generated plan
- REST API endpoints ready for a future Supabase backend
- Health check and dataset statistics endpoints
- Gunicorn deployment command for Render
- No MongoDB, SQLite or Supabase connection is required to run the starter version

## Dataset

The supplied dataset is stored at:

`data/NutriAI_Final_Dataset_Food_Catalog.csv`

The application reads it directly. It contains 1,331 records at the time this project was generated.

The loader uses `latin1` because the uploaded CSV contains a non-UTF-8 byte. Do not convert the dataset to another format unless necessary.

## Run locally

Windows PowerShell:

```powershell
cd path\to\NutriAI_AI_Assisted_Diet_Recommendation
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Then open:

`http://127.0.0.1:5000`

If PowerShell blocks activation, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

## Render deployment

Create a GitHub repository and upload the project files.

Render settings:

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn run:app`
- Root directory: leave blank

No database environment variables are needed for the current version.

## Supabase integration later

The current project deliberately does not connect to Supabase. This avoids the connection/password/TLS problems while you develop the recommendation engine.

When you are ready, add Supabase using an environment-based service layer. Recommended future tables:

### profiles
- id (uuid, primary key)
- age
- height_cm
- weight_kg
- diet
- activity
- goal
- created_at

### meal_plans
- id (uuid, primary key)
- user_id (uuid, foreign key)
- target_calories
- plan_json
- created_at

### saved_meals
- id (uuid, primary key)
- user_id
- food_name
- meal_slot
- created_at

Do NOT commit `.env` or Supabase secret/service keys to GitHub.

## API endpoints

- `GET /api/health`
- `GET /api/stats`
- `GET /api/search?q=`
- `GET /api/recipe?name=`
- `POST /api/plan`
- `POST /api/swap`

## Important project note

This is an educational diet-recommendation software project, not a medical or clinical nutrition system. Nutrition values are based on the supplied dataset and may need verification before real-world health use.
