
import os
import psycopg
from werkzeug.security import generate_password_hash, check_password_hash


def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    return psycopg.connect(database_url)


def create_user(email, password):
    email = email.strip().lower()

    if not email or "@" not in email or "." not in email.split("@", 1)[-1]:
        return False, "Enter a valid email address."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.app_users (email, password_hash)
                    VALUES (%s, %s)
                    ON CONFLICT (email) DO NOTHING
                    RETURNING id
                    """,
                    (email, password_hash)
                )

                if cur.fetchone() is None:
                    return False, "An account with this email already exists."

        return True, "Account created successfully. You can now log in."

    except psycopg.Error as e:
        print("SUPABASE SIGNUP ERROR:", repr(e))
        return False, "Database error. Check the Flask terminal."


def authenticate(email, password):
    email = email.strip().lower()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT password_hash
                    FROM public.app_users
                    WHERE email = %s
                    """,
                    (email,)
                )

                user = cur.fetchone()

        return bool(
            user and check_password_hash(user[0], password)
        )

    except psycopg.Error as e:
        print("SUPABASE LOGIN ERROR:", repr(e))
        return False