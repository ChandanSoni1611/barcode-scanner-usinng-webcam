import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "scanner.db"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))