from pathlib import Path
import pandas as pd
import json
import math
import numpy as np

REQUIRED = ["name", "meal_category", "diet_type", "calories_kcal",
            "protein_g", "carbohydrates_g", "fats_g", "fibre_g", "ingredients_text"]

def load_foods(path: Path):
    # Dataset contains some non-UTF-8 source characters, so latin-1 is used as a lossless
    # single-byte fallback for this supplied catalog.
    df = pd.read_csv(path, encoding="latin1")
    for c in ["calories_kcal","protein_g","carbohydrates_g","fats_g","fibre_g","serving_size_g"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    for c in REQUIRED:
        if c not in df.columns:
            df[c] = ""
    df["name"] = df["name"].fillna("").astype(str).str.strip()
    df = df[df["name"] != ""].copy()
    df["meal_category"] = df["meal_category"].fillna("main").astype(str).str.lower().str.strip()
    df["diet_type"] = df["diet_type"].fillna("vegetarian").astype(str).str.lower().str.strip()
    df["region"] = df.get("region", pd.Series([""]*len(df))).fillna("").astype(str).str.strip()
    df["ingredients_text"] = df["ingredients_text"].fillna("").astype(str)
    # Remove exact duplicate dish names while retaining the first source record.
    df = df.drop_duplicates(subset=["name"], keep="first").reset_index(drop=True)
    return df

def food_to_dict(row):
    def clean(v):
        if pd.isna(v): return ""
        if isinstance(v, (float, np.floating)):
            return round(float(v), 2)
        return str(v)
    return {
        "id": int(row.name),
        "name": clean(row["name"]),
        "category": clean(row["meal_category"]),
        "diet": clean(row["diet_type"]),
        "region": clean(row.get("region","")),
        "calories": clean(row["calories_kcal"]),
        "protein": clean(row["protein_g"]),
        "carbs": clean(row["carbohydrates_g"]),
        "fat": clean(row["fats_g"]),
        "fibre": clean(row["fibre_g"]),
        "serving": clean(row.get("serving_description","")),
        "ingredients": clean(row["ingredients_text"]),
    }
