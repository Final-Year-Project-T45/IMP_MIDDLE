import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Auto-search and load .env files from backend/.env or root .env
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")
load_dotenv(".env")

class Settings(BaseSettings):
    GROQ_API_KEY: Optional[str] = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DATABASE_URL: str = "sqlite:///./finsecure.db"
    POLICIES_DIR: str = "../policies_data"
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure environment override takes precedence if loaded by load_dotenv
        if os.getenv("GROQ_API_KEY"):
            self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        if os.getenv("GROQ_MODEL"):
            self.GROQ_MODEL = os.getenv("GROQ_MODEL")

settings = Settings()

