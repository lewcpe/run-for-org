from fastapi import FastAPI
from .config import get_settings
from .routers import users, stats

settings = get_settings()

app = FastAPI(
    title="Run for Organization",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(stats.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Run for Organization API"}

@app.get("/api/config")
def get_public_config():
    return {
        "start_date": settings.RUNORG_START_DATE,
        "end_date": settings.RUNORG_END_DATE,
        "total_step_goal": settings.RUNORG_TOTAL_STEP_GOAL,
        "step_per_km": settings.RUNORG_STEP_PER_KM,
        "top_user_limit": settings.RUNORG_TOP_USER
    }
