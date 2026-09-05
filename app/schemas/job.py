from typing import Optional, Any, Dict
from pydantic import BaseModel

class JobProgress(BaseModel):
    percentage: float = 0.0
    phase: str = "Queued"
    speed: Optional[str] = None
    eta: Optional[int] = None

class JobDto(BaseModel):
    id: str
    url: str
    type: str
    quality: str
    status: str
    progress: JobProgress
    filename: Optional[str] = None
    downloadUrl: Optional[str] = None
    error: Optional[str] = None

class JobCreateRequest(BaseModel):
    url: str
    type: Optional[str] = "video"
    quality: Optional[str] = "1080p"

class JobCreateResponse(BaseModel):
    success: bool = True
    job: JobDto

class JobStatusResponse(BaseModel):
    success: bool = True
    job: JobDto
