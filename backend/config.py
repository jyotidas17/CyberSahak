import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "cybersahak_db")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    JWT_SECRET = os.getenv("JWT_SECRET")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    URLHAUS_AUTH_KEY = os.getenv("URLHAUS_AUTH_KEY")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    ALLOW_DEMO_PASSWORD_RESET = os.getenv("ALLOW_DEMO_PASSWORD_RESET", "false").lower() == "true"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    @classmethod
    def validate(cls):
        missing = [name for name in ("DB_USER", "DB_PASSWORD", "JWT_SECRET") if not getattr(cls, name)]
        if missing:
            raise RuntimeError("Missing required configuration: " + ", ".join(missing))
