"""
Fitness Buddy - Application Configuration
Loads settings from environment variables via .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Always load from the .env file in this directory, overriding any existing env vars
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

class Config:
    # ── Core Flask ───────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    FLASK_ENV  = os.environ.get("FLASK_ENV", "development")

    # ── Database ─────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///fitness_buddy.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── IBM watsonx.ai ────────────────────────────────────────
    IBM_API_KEY          = os.environ.get("IBM_API_KEY", "")
    IBM_PROJECT_ID       = os.environ.get("IBM_PROJECT_ID", "")
    IBM_WATSONX_URL      = os.environ.get(
        "IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"
    )
    IBM_GRANITE_MODEL_ID = os.environ.get(
        "IBM_GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2"
    )

    # ── App Settings ──────────────────────────────────────────
    APP_NAME              = os.environ.get("APP_NAME", "Fitness Buddy")
    MAX_CHAT_HISTORY      = int(os.environ.get("MAX_CHAT_HISTORY", 50))
    SESSION_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", 60))

    # ── File Uploads ──────────────────────────────────────────
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB
    UPLOAD_FOLDER      = os.path.join(os.path.dirname(__file__), "static", "images")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///fitness_buddy.db")


config_by_name = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
}

def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
