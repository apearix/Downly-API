import time
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class JobProgress(BaseModel):
    percentage: float = 0.0
    phase: str = "Queued"
    speed: Optional[str] = None
    eta: Optional[str] = None
    downloadedBytes: Optional[int] = None
    totalBytes: Optional[int] = None

class JobDto(BaseModel):
    id: str
    url: str
    type: str
    quality: str
    status: str
    progress: JobProgress
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    channel: Optional[str] = None
    filename: Optional[str] = None
    fileSize: Optional[int] = None
    outputFormat: Optional[str] = None
    downloadUrl: Optional[str] = None
    error: Optional[str] = None
    createdAt: int = Field(default_factory=lambda: int(time.time() * 1000))
    updatedAt: int = Field(default_factory=lambda: int(time.time() * 1000))
    expiresAt: int = Field(default_factory=lambda: int(time.time() * 1000) + 1800000)

class JobCreateRequest(BaseModel):
    url: str
    type: Optional[str] = "video"
    quality: Optional[str] = "1080p"

class JobCreateResponse(BaseModel):
    success: bool = True
    jobId: str
    job: JobDto

class JobStatusResponse(BaseModel):
    success: bool = True
    job: JobDto
