from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
