
import os
import json
import psycopg


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    return psycopg.connect(database_url)


def save_user_profile(user_id, profile):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.user_profiles
                (user_id, age, height_cm, weight_kg,
                 dietary_preference, food_allergies)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    age = EXCLUDED.age,
                    height_cm = EXCLUDED.height_cm,
                    weight_kg = EXCLUDED.weight_kg,
                    dietary_preference = EXCLUDED.dietary_preference,
                    food_allergies = EXCLUDED.food_allergies,
                    updated_at = NOW()
                """,
                (
                    user_id,
                    profile.get("age"),
                    profile.get("height"),
                    profile.get("weight"),
                    profile.get("dietary_preference"),
                    profile.get("food_allergies")
                )
            )


def save_meal_plan(user_id, plan):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.meal_plans (user_id, plan_data)
                VALUES (%s, %s)
                RETURNING id
                """,
                (user_id, json.dumps(plan))
            )
            return cur.fetchone()[0]


def save_meal_history(user_id, plan):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.meal_history (user_id, plan_data)
                VALUES (%s, %s)
                """,
                (user_id, json.dumps(plan))
            )


def get_meal_history(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, plan_data, generated_at
                FROM public.meal_history
                WHERE user_id = %s
                ORDER BY generated_at DESC
                """,
                (user_id,)
            )
            return cur.fetchall()


def save_favourite_meal(user_id, meal_name, meal_data):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.saved_meals
                (user_id, meal_name, meal_data)
                VALUES (%s, %s, %s)
                """,
                (user_id, meal_name, json.dumps(meal_data))
            )


def get_saved_meals(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, meal_name, meal_data, created_at
                FROM public.saved_meals
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            return cur.fetchall()
def get_user_id(email):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM public.app_users
                WHERE email = %s
                """,
                (email.strip().lower(),)
            )
            user = cur.fetchone()

    return user[0] if user else None

def delete_favourite_meal(user_id, meal_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM public.saved_meals
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (meal_id, user_id)
            )
            return cur.fetchone() is not None