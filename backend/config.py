from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    
    # Run Organization Config
    RUNORG_START_DATE: str = "2023-01-01"
    RUNORG_END_DATE: str = "2023-12-31"
    RUNORG_TOTAL_STEP_GOAL: int = 1000000
    RUNORG_STEP_PER_KM: int = 1500
    RUNORG_TOP_USER: int = 5
    
    # Auth Config
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""
    FIREBASE_PROJECT_ID: str = ""

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings():
    return Settings()
