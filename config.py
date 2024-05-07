import os
from dotenv import load_dotenv


class Config:
    # Load environment variables
    load_dotenv()
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default_secret_key")
    SESSION_NAME = os.getenv("FLASK_SESSION_NAME", "default_session_name")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", None)
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET_KEY", None)
    SPOTIFY_REDIRECT_URI = None


class DevelopmentConfig(Config):
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI_DEV", "http://127.0.0.1:5000/authorize")


class ProductionConfig(Config):
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI_PROD", "https://spotify-dance.vercel.app/authorize")


def get_config():
    """Return the appropriate config based on FLASK_ENV"""
    flask_env = os.getenv("FLASK_ENV", "production").lower()
    if flask_env == "development":
        return DevelopmentConfig()
    return ProductionConfig
