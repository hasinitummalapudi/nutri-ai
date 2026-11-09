from flask import Flask
from pathlib import Path

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = __import__("os").environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["DATA_PATH"] = Path(app.root_path).parent / "data" / "NutriAI_Final_Dataset_Food_Catalog.csv"

    from .routes import bp
    app.register_blueprint(bp)
    return app
