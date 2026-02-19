from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, config
from ..database import get_db

router = APIRouter(
    prefix="/api/stats",
    tags=["stats"],
    responses={404: {"description": "Not found"}},
)

settings = config.get_settings()

@router.get("/progress", response_model=schemas.OrganizationProgress)
def read_organization_progress(db: Session = Depends(get_db)):
    return crud.get_organization_stats(db, settings.RUNORG_TOTAL_STEP_GOAL)

@router.get("/weekly", response_model=List[schemas.WeeklyStats])
def read_weekly_stats(db: Session = Depends(get_db)):
    return crud.get_weekly_stats(db)

@router.get("/leaderboard", response_model=List[schemas.LeaderboardEntry])
def read_leaderboard(db: Session = Depends(get_db)):
    leaderboard = crud.get_leaderboard(db, settings.RUNORG_TOP_USER)
    # Mask emails
    result = []
    for entry in leaderboard:
        user = entry["user"]
        email_parts = user.email.split("@")
        if len(email_parts) == 2:
            masked = f"{email_parts[0][:3]}***@{email_parts[1]}"
        else:
            masked = user.email
            
        result.append({
            "rank": 0, # Rank assigned in logic or frontend. Let's assign here.
            "email_masked": masked,
            "name": f"{user.firstname} {user.lastname}" if user.firstname and user.lastname else None,
            "steps": entry["steps"]
        })
    
    # Add ranks
    for i, item in enumerate(result):
        item["rank"] = i + 1
        
    return result
