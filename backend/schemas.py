from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class RunningLogBase(BaseModel):
    running_datetime: datetime
    step_count: Optional[int] = None
    distance_km: Optional[float] = None

class RunningLogCreate(RunningLogBase):
    pass

class RunningLogUpdate(RunningLogBase):
    pass

class RunningLog(RunningLogBase):
    id: int
    owner_id: int
    created_at: datetime
    step_count: int
    distance_km: float

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None

class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    logs: List[RunningLog] = []

    model_config = ConfigDict(from_attributes=True)

class UserStats(BaseModel):
    email: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    total_steps: int
    total_distance: float

class WeeklyStats(BaseModel):
    week: str
    steps: int

class LeaderboardEntry(BaseModel):
    rank: int
    email_masked: str
    name: Optional[str] = None
    steps: int

class OrganizationProgress(BaseModel):
    percentage: float
    total_steps: int
    goal: int
