import random
import re
from collections import defaultdict

MEAL_ALIASES = {
    "breakfast": ["breakfast"],
    "lunch": ["lunch", "main", "rice"],
    "dinner": ["dinner", "main"],
    "snack": ["snack", "beverage", "dessert"],
}

def normalize(s):
    return re.sub(r"[^a-z0-9 ]+", " ", str(s).lower()).strip()

def filter_diet(df, diet):
    diet = (diet or "vegetarian").lower()
    if diet == "vegetarian":
        return df[df["diet_type"].str.contains("vegetarian", na=False)]
    if diet == "vegan":
        return df[df["diet_type"].str.contains("vegan", na=False)]
    if diet in ("non-vegetarian", "non vegetarian"):
        return df[df["diet_type"].str.contains("non|non-vegetarian|omnivore", na=False, regex=True)]
    return df

def choose_pool(df, slot, used_names, diet):
    pool = filter_diet(df, diet)
    terms = MEAL_ALIASES.get(slot, [slot])
    mask = pool["meal_category"].apply(lambda x: any(t in normalize(x) for t in terms))
    candidates = pool[mask].copy()
    if len(candidates) < 5:
        candidates = pool.copy()
    candidates = candidates[~candidates["name"].isin(used_names)]
    return candidates

def target_calories(profile):
    # Simple transparent estimate for a demo recommendation engine.
    age = float(profile.get("age") or 25)
    height = float(profile.get("height") or 165)
    weight = float(profile.get("weight") or 65)
    activity = profile.get("activity", "moderate")
    goal = profile.get("goal", "maintain")
    # Adult-only app: Mifflin-St Jeor uses a neutral baseline because sex is not required.
    bmr = 10*weight + 6.25*height - 5*age + 5
    factor = {"low":1.2, "light":1.35, "moderate":1.5, "high":1.7}.get(activity, 1.5)
    tdee = bmr * factor
    if goal == "lose": tdee -= 250
    elif goal == "gain": tdee += 250
    return max(1200, min(3500, round(tdee)))

def recommend_week(df, profile, seed=None):
    rng = random.Random(seed if seed is not None else random.randint(1, 10_000_000))
    daily = target_calories(profile)
    slots = [("breakfast", .25), ("lunch", .35), ("snack", .10), ("dinner", .30)]
    used = set()
    week = []
    for day in range(7):
        meals=[]
        # Prefer unseen dishes for every day; relax only if the dataset pool is small.
        for slot, share in slots:
            pool = choose_pool(df, slot, used, profile.get("diet"))
            if pool.empty:
                pool = filter_diet(df, profile.get("diet")).copy()
            if pool.empty:
                continue
            # Score calories against the day's share, with a little randomization for variety.
            target = daily*share
            p = pool.copy()
            p["dist"] = (p["calories_kcal"] - target).abs()
            top = p.nsmallest(min(12, len(p)), "dist")
            idx = rng.randrange(len(top))
            row = top.iloc[idx]
            used.add(row["name"])
            meals.append({
                "slot": slot, "name": str(row["name"]), "category": str(row["meal_category"]),
                "diet": str(row["diet_type"]), "calories": round(float(row["calories_kcal"]),1),
                "protein": round(float(row["protein_g"]),1), "carbs": round(float(row["carbohydrates_g"]),1),
                "fat": round(float(row["fats_g"]),1), "fibre": round(float(row["fibre_g"]),1),
                "ingredients": str(row["ingredients_text"] or "")
            })
        week.append({"day": day+1, "meals": meals})
    return {"target_calories": daily, "days": week}

def swap_meal(df, current_name, slot, profile, seed=None):
    pool = choose_pool(df, slot, {current_name}, profile.get("diet"))
    if pool.empty:
        pool = filter_diet(df, profile.get("diet"))
    if pool.empty: return None
    rng=random.Random(seed)
    # choose among 15 closest-to-slot-calorie options, then randomize
    daily=target_calories(profile)
    target=daily*dict([("breakfast",.25),("lunch",.35),("snack",.1),("dinner",.3)]).get(slot,.25)
    p=pool.copy(); p["dist"]=(p["calories_kcal"]-target).abs()
    top=p.nsmallest(min(15,len(p)),"dist")
    row=top.iloc[rng.randrange(len(top))]
    return {
        "name": str(row["name"]), "category": str(row["meal_category"]),
        "diet": str(row["diet_type"]), "calories": round(float(row["calories_kcal"]),1),
        "protein": round(float(row["protein_g"]),1), "carbs": round(float(row["carbohydrates_g"]),1),
        "fat": round(float(row["fats_g"]),1), "fibre": round(float(row["fibre_g"]),1),
        "ingredients": str(row["ingredients_text"] or "")
    }
