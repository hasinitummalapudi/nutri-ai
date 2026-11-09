
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from .data_loader import load_foods, food_to_dict
from .recommender import recommend_week, swap_meal
from .auth import create_user, authenticate

from .database import (
    get_user_id,
    save_user_profile,
    save_meal_plan,
    save_meal_history,
    get_meal_history,
    save_favourite_meal,
    get_saved_meals,
    delete_favourite_meal
)


bp = Blueprint("main", __name__)

_df_cache = None


# --------------------------------
# FOOD DATA
# --------------------------------

def foods():
    global _df_cache

    if _df_cache is None:
        _df_cache = load_foods(current_app.config["DATA_PATH"])

    return _df_cache


# --------------------------------
# LOGIN PROTECTION
# --------------------------------

def logged_in():
    return bool(session.get("user_email"))


def protected_api():
    if not logged_in():
        return jsonify(error="Please log in to use NutriAI."), 401

    return None


# --------------------------------
# HOME AND AUTHENTICATION
# --------------------------------

@bp.get("/")
def index():
    if not logged_in():
        return redirect(url_for("main.login_page"))

    return render_template(
        "index.html",
        email=session.get("user_email")
    )


@bp.get("/login")
def login_page():
    if logged_in():
        return redirect(url_for("main.index"))

    return render_template("auth.html", mode="login")


@bp.get("/signup")
def signup_page():
    if logged_in():
        return redirect(url_for("main.index"))

    return render_template("auth.html", mode="signup")


@bp.post("/api/signup")
def signup():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", ""))
    password = str(data.get("password", ""))

    ok, message = create_user(email, password)

    if not ok:
        return jsonify(error=message), 400

    return jsonify(message=message)


@bp.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not authenticate(email, password):
        return jsonify(error="Incorrect email or password."), 401

    session.clear()
    session["user_email"] = email

    return jsonify(message="Login successful.")


@bp.post("/api/logout")
def logout():
    session.clear()

    return jsonify(message="Logged out.")


@bp.get("/api/me")
def me():
    if not logged_in():
        return jsonify(logged_in=False), 401

    return jsonify(
        logged_in=True,
        email=session.get("user_email")
    )


# --------------------------------
# HEALTH AND STATISTICS
# --------------------------------

@bp.get("/api/health")
def health():
    return jsonify(
        status="ok",
        message="NutriAI is running",
        dataset_items=len(foods())
    )


@bp.get("/api/stats")
def stats():
    guard = protected_api()

    if guard:
        return guard

    df = foods()

    return jsonify({
        "foods": int(len(df)),
        "categories": sorted([
            str(x) for x in df["meal_category"].dropna().unique()
        ]),
        "diets": sorted([
            str(x) for x in df["diet_type"].dropna().unique()
        ]),
        "regions": sorted([
            str(x)
            for x in df["region"].dropna().unique()
            if str(x).strip()
        ])
    })


# --------------------------------
# GENERATE MEAL PLAN
# --------------------------------

@bp.post("/api/plan")
def plan():
    guard = protected_api()

    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    required = ["age", "height", "weight"]

    if any(not data.get(k) for k in required):
        return jsonify(
            error="Age, height and weight are required."
        ), 400

    try:
        if not (18 <= float(data["age"]) <= 100):
            raise ValueError

        if not (100 <= float(data["height"]) <= 230):
            raise ValueError

        if not (25 <= float(data["weight"]) <= 300):
            raise ValueError

    except (ValueError, TypeError):
        return jsonify(
            error="Enter realistic adult profile values."
        ), 400

    try:
        user_id = get_user_id(session["user_email"])

        if not user_id:
            return jsonify(error="User account not found."), 404

        result = recommend_week(foods(), data)

        profile_data = {
            **data,
            "dietary_preference": data.get("dietary_preference") or data.get("diet"),
            "food_allergies": data.get("food_allergies")
        }

        save_user_profile(user_id, profile_data)
        save_meal_plan(user_id, result)
        save_meal_history(user_id, result)

        return jsonify(result)

    except Exception as e:
        current_app.logger.exception(
            "MEAL PLAN DATABASE ERROR"
        )

        return jsonify(
            error="Unable to generate or save meal plan. Check the Flask terminal."
        ), 500


# --------------------------------
# SWAP MEAL
# --------------------------------

@bp.post("/api/swap")
def swap():
    guard = protected_api()

    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    result = swap_meal(
        foods(),
        data.get("current_name", ""),
        data.get("slot", "lunch"),
        data.get("profile") or {},
        data.get("seed")
    )

    if not result:
        return jsonify(error="No alternative found."), 404

    return jsonify(result)


# --------------------------------
# FOOD SEARCH
# --------------------------------

@bp.get("/api/search")
def search():
    guard = protected_api()

    if guard:
        return guard

    q = (request.args.get("q") or "").strip().lower()
    diet = (request.args.get("diet") or "").strip().lower()

    df = foods()

    if q:
        df = df[
            df["name"].str.lower().str.contains(q, na=False)
        ]

    if diet and diet != "all":
        df = df[
            df["diet_type"].str.lower().str.contains(diet, na=False)
        ]

    return jsonify([
        food_to_dict(row)
        for _, row in df.head(30).iterrows()
    ])


# --------------------------------
# RECIPE DETAILS
# --------------------------------

@bp.get("/api/recipe")
def recipe():
    guard = protected_api()

    if guard:
        return guard

    name = request.args.get("name", "").strip().lower()

    df = foods()

    hit = df[df["name"].str.lower() == name]

    if hit.empty:
        hit = df[
            df["name"].str.lower().str.contains(name, na=False)
        ].head(1)

    if hit.empty:
        return jsonify(error="Recipe not found."), 404

    row = hit.iloc[0]

    ingredients = [
        x.strip()
        for x in str(row["ingredients_text"] or "").split(";")
        if x.strip()
    ]

    return jsonify({
        "name": str(row["name"]),
        "ingredients": ingredients,
        "category": str(row["meal_category"]),
        "diet": str(row["diet_type"]),
        "calories": round(float(row["calories_kcal"]), 1),
        "protein": round(float(row["protein_g"]), 1),
        "carbs": round(float(row["carbohydrates_g"]), 1),
        "fat": round(float(row["fats_g"]), 1),
        "fibre": round(float(row["fibre_g"]), 1),
        "serving": str(row.get("serving_description", ""))
    })


# --------------------------------
# MEAL HISTORY
# --------------------------------

@bp.get("/api/history")
def meal_history():
    guard = protected_api()

    if guard:
        return guard

    try:
        user_id = get_user_id(session["user_email"])

        if not user_id:
            return jsonify(error="User account not found."), 404

        records = get_meal_history(user_id)

        return jsonify([
            {
                "id": row[0],
                "plan": row[1],
                "generated_at": (
                    row[2].isoformat() if row[2] else None
                )
            }
            for row in records
        ])

    except Exception:
        current_app.logger.exception("HISTORY ERROR")

        return jsonify(
            error="Unable to load meal history."
        ), 500


# --------------------------------
# SAVE FAVOURITE MEAL
# --------------------------------

@bp.post("/api/saved-meals")
def add_saved_meal():
    guard = protected_api()

    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    meal_name = str(data.get("meal_name", "")).strip()
    meal_data = data.get("meal_data") or {}

    if not meal_name:
        return jsonify(error="Meal name is required."), 400

    if not isinstance(meal_data, dict):
        return jsonify(error="Invalid meal data."), 400

    try:
        user_id = get_user_id(session["user_email"])

        if not user_id:
            return jsonify(error="User account not found."), 404

        save_favourite_meal(
            user_id,
            meal_name,
            meal_data
        )

        return jsonify(
            message="Meal saved successfully."
        )

    except Exception:
        current_app.logger.exception("SAVE MEAL ERROR")

        return jsonify(
            error="Unable to save meal."
        ), 500


# --------------------------------
# GET SAVED MEALS
# --------------------------------

@bp.get("/api/saved-meals")
def list_saved_meals():
    guard = protected_api()

    if guard:
        return guard

    try:
        user_id = get_user_id(session["user_email"])

        if not user_id:
            return jsonify(error="User account not found."), 404

        records = get_saved_meals(user_id)

        return jsonify([
            {
                "id": row[0],
                "meal_name": row[1],
                "meal_data": row[2],
                "created_at": (
                    row[3].isoformat() if row[3] else None
                )
            }
            for row in records
        ])

    except Exception:
        current_app.logger.exception("GET SAVED MEALS ERROR")

        return jsonify(
            error="Unable to load saved meals."
        ), 500


# --------------------------------
# DELETE SAVED MEAL
# --------------------------------

@bp.delete("/api/saved-meals/<int:meal_id>")
def remove_saved_meal(meal_id):
    guard = protected_api()

    if guard:
        return guard

    try:
        user_id = get_user_id(session["user_email"])

        if not user_id:
            return jsonify(error="User account not found."), 404

        deleted = delete_favourite_meal(
            user_id,
            meal_id
        )

        if not deleted:
            return jsonify(
                error="Saved meal not found."
            ), 404

        return jsonify(
            message="Meal removed successfully."
        )

    except Exception:
        current_app.logger.exception("DELETE MEAL ERROR")

        return jsonify(
            error="Unable to remove meal."
        ), 500
