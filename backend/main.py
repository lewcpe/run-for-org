from fastapi import FastAPI, Request
from .config import get_settings
from .routers import users, stats, auth as auth_router
from . import auth as auth_utils

settings = get_settings()

app = FastAPI(
    title="Run for Organization",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(stats.router)
app.include_router(auth_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Run for Organization API"}

@app.get("/api/config")
def get_public_config(request: Request):
    callback_url = settings.OIDC_CALLBACK_URL or str(request.url_for("auth_callback"))
    return {
        "start_date": settings.RUNORG_START_DATE,
        "end_date": settings.RUNORG_END_DATE,
        "total_step_goal": settings.RUNORG_TOTAL_STEP_GOAL,
        "step_per_km": settings.RUNORG_STEP_PER_KM,
        "top_user_limit": settings.RUNORG_TOP_USER,
        "oidc_issuer": settings.OIDC_ISSUER,
        "oidc_client_id": settings.OIDC_CLIENT_ID,
        "oidc_callback_url": callback_url,
        "oidc_login_url": settings.OIDC_AUTH_URL or auth_utils.get_oidc_config_url(settings.OIDC_ISSUER)
    }
