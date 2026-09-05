from typing import Optional
from pydantic import BaseModel

class DownloadRequest(BaseModel):
    url: str
    type: Optional[str] = "video"
    quality: Optional[str] = "1080p"
