import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gemini-2.5-flash") # Cost-efficient and fast for structured text extraction

# Scraping & Processing Defaults
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "India")
DEFAULT_RESULTS_LIMIT = int(
    os.getenv("DEFAULT_RESULTS_LIMIT", "20")
)

if DEFAULT_RESULTS_LIMIT < 1:
    raise ValueError("DEFAULT_RESULTS_LIMIT must be at least 1")

# Database path
SQLITE_DB_PATH = BASE_DIR / "data" / "jobs_database.sqlite"