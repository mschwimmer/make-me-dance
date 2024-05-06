import os
from dotenv import load_dotenv


class Config:
    # Load environment variables
    load_dotenv()
    FLASK_SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    FLASK_SESSION_NAME = os.getenv("SESSION_NAME", "default_session_name")
    FLASK_DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", None)
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET_KEY", None)


