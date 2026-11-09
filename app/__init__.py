
import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv


def create_app():
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / ".env", override=True)

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "dev-secret-change-me"
    )

    app.config["DATA_PATH"] = (
        BASE_DIR / "data" / "NutriAI_Final_Dataset_Food_Catalog.csv"
    )

    from .routes import bp
    app.register_blueprint(bp)

    return app
