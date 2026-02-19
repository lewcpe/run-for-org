from sqlalchemy.orm import Session
from . import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str):
    db_user = models.User(email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: models.User, user_update: schemas.UserUpdate):
    if user_update.firstname is not None:
        user.firstname = user_update.firstname
    if user_update.lastname is not None:
        user.lastname = user_update.lastname
    db.commit()
    db.refresh(user)
    return user

def create_audit_log(db: Session, user_id: int, message: str):
    db_log = models.AuditLog(user_id=user_id, message=message)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_running_logs(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.RunningLog).filter(models.RunningLog.owner_id == user_id).offset(skip).limit(limit).all()

def create_running_log(db: Session, log: models.RunningLog, user_id: int):
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_running_log(db: Session, log_id: int, user_id: int):
    return db.query(models.RunningLog).filter(models.RunningLog.id == log_id, models.RunningLog.owner_id == user_id).first()

def delete_running_log(db: Session, log_id: int, user_id: int):
    log = get_running_log(db, log_id, user_id)
    if log:
        db.delete(log)
        db.commit()
    return log

def get_user_stats(db: Session, user_id: int):
    logs = db.query(models.RunningLog).filter(models.RunningLog.owner_id == user_id).all()
    total_steps = sum(log.step_count for log in logs)
    total_distance = sum(log.distance_km for log in logs)
    return {"total_steps": total_steps, "total_distance": total_distance}

def get_organization_stats(db: Session, goal: int):
    total_steps = db.query(models.RunningLog).with_entities(models.RunningLog.step_count).all()
    total_steps_sum = sum(step[0] for step in total_steps)
    percentage = (total_steps_sum / goal) * 100 if goal > 0 else 0
    return {"total_steps": total_steps_sum, "percentage": percentage, "goal": goal}

def get_leaderboard(db: Session, limit: int = 5):
    # This is a naive implementation. For large datasets, use SQL aggregation.
    users = db.query(models.User).all()
    leaderboard = []
    for user in users:
        stats = get_user_stats(db, user.id)
        leaderboard.append({"user": user, "steps": stats["total_steps"]})
    
    leaderboard.sort(key=lambda x: x["steps"], reverse=True)
    return leaderboard[:limit]

def get_weekly_stats(db: Session):
    # Naive implementation. Use SQL group by for efficiency.
    logs = db.query(models.RunningLog).all()
    weekly_data = {}
    for log in logs:
        # ISO week format: "YYYY-Www"
        week = log.running_datetime.strftime("%Y-W%W")
        if week not in weekly_data:
            weekly_data[week] = 0
        weekly_data[week] += log.step_count
        
    sorted_weeks = sorted(weekly_data.items())
    return [{"week": k, "steps": v} for k, v in sorted_weeks]

def get_user_weekly_stats(db: Session, user_id: int):
    logs = db.query(models.RunningLog).filter(models.RunningLog.owner_id == user_id).all()
    weekly_data = {}
    for log in logs:
        week = log.running_datetime.strftime("%Y-W%W")
        if week not in weekly_data:
            weekly_data[week] = 0
        weekly_data[week] += log.step_count
        
    sorted_weeks = sorted(weekly_data.items())
    return [{"week": k, "steps": v} for k, v in sorted_weeks]
