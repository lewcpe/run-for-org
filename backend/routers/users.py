from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, config
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(
    prefix="/api/me",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

settings = config.get_settings()

@router.get("", response_model=schemas.UserStats)
def read_user_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = crud.get_user_stats(db, current_user.id)
    return {
        "email": current_user.email,
        "firstname": current_user.firstname,
        "lastname": current_user.lastname,
        "total_steps": stats["total_steps"],
        "total_distance": stats["total_distance"]
    }

@router.put("", response_model=schemas.User)
def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_user = crud.update_user(db, current_user, user_update)
    crud.create_audit_log(db, user_id=current_user.id, message="Updated user profile")
    return updated_user

@router.get("/logs", response_model=List[schemas.RunningLog])
def read_running_logs(
    skip: int = 0, 
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = crud.get_running_logs(db, user_id=current_user.id, skip=skip, limit=limit)
    return logs

@router.post("/logs", response_model=schemas.RunningLog)
def create_running_log(
    log: schemas.RunningLogCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Auto calculation logic
    step_count = log.step_count
    distance_km = log.distance_km
    
    if step_count is None and distance_km is None:
        raise HTTPException(status_code=400, detail="Either step_count or distance_km must be provided")
        
    if step_count is None:
        step_count = int(distance_km * settings.RUNORG_STEP_PER_KM)
        
    if distance_km is None:
        distance_km = step_count / settings.RUNORG_STEP_PER_KM

    db_log = models.RunningLog(
        owner_id=current_user.id,
        running_datetime=log.running_datetime,
        step_count=step_count,
        distance_km=distance_km
    )
    created_log = crud.create_running_log(db, log=db_log, user_id=current_user.id)
    crud.create_audit_log(db, user_id=current_user.id, message=f"Created log id {created_log.id}")
    return created_log

@router.put("/logs/{log_id}", response_model=schemas.RunningLog)
def update_running_log(
    log_id: int,
    log_update: schemas.RunningLogUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_log = crud.get_running_log(db, log_id, current_user.id)
    if db_log is None:
        raise HTTPException(status_code=404, detail="Log not found")

    step_count = log_update.step_count
    distance_km = log_update.distance_km

    if step_count is None and distance_km is None:
         raise HTTPException(status_code=400, detail="Either step_count or distance_km must be provided for update")

    if step_count is not None and distance_km is None:
         distance_km = step_count / settings.RUNORG_STEP_PER_KM
    elif distance_km is not None and step_count is None:
         step_count = int(distance_km * settings.RUNORG_STEP_PER_KM)
         
    # Update fields
    if step_count is not None:
        db_log.step_count = step_count
    if distance_km is not None:
        db_log.distance_km = distance_km
    if log_update.running_datetime:
        db_log.running_datetime = log_update.running_datetime
        
    db.commit()
    db.refresh(db_log)
    crud.create_audit_log(db, user_id=current_user.id, message=f"Updated log id {db_log.id}")
    return db_log

@router.delete("/logs/{log_id}", response_model=schemas.RunningLog)
def delete_running_log(
    log_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_log = crud.delete_running_log(db, log_id, current_user.id)
    if db_log is None:
        raise HTTPException(status_code=404, detail="Log not found")
    crud.create_audit_log(db, user_id=current_user.id, message=f"Deleted log id {log_id}")
    return db_log

@router.get("/weekly", response_model=List[schemas.WeeklyStats])
def read_user_weekly_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_weekly_stats(db, current_user.id)
