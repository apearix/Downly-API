from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class QualityOption(BaseModel):
    id: str
    label: str
    height: int

class InfoRequest(BaseModel):
    url: str

class MediaInfoResponse(BaseModel):
    success: bool = True
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    channel: Optional[str] = None
    qualities: List[QualityOption] = []
