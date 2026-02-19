from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List

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
    
    # Generic OIDC Config
    OIDC_ISSUER: str = ""
    OIDC_AUDIENCE: str = ""
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""
    OIDC_CALLBACK_URL: str = ""
    OIDC_CALLBACK_URL: str = ""
    OIDC_ALGORITHMS: List[str] = ["RS256"]
    OIDC_AUTH_URL: str = "" # Optional, for frontend redirect
    
    # Internal JWT Config
    RUNORG_JWT_SECRET: str = "change-this-to-secure-random-secret"
    RUNORG_JWT_ALGORITHM: str = "HS256"
    RUNORG_JWT_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings():
    return Settings()
