from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.info import InfoRequest, MediaInfoResponse
from app.core.url import validate_and_normalize_youtube_url
from app.services.ytdlp_service import extract_video_info

router = APIRouter(prefix="/api", tags=["info"])

@router.get("/info", response_model=MediaInfoResponse)
async def get_info_query(url: str = Query(..., description="YouTube Video or Shorts URL")):
    is_valid, normalized_url, error = validate_and_normalize_youtube_url(url)
    if not is_valid or not normalized_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid YouTube URL.")

    try:
        info = extract_video_info(normalized_url)
        return MediaInfoResponse(success=True, **info)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve information for this YouTube video: {str(exc)}"
        )

@router.post("/info", response_model=MediaInfoResponse)
async def get_info_body(payload: InfoRequest):
    is_valid, normalized_url, error = validate_and_normalize_youtube_url(payload.url)
    if not is_valid or not normalized_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid YouTube URL.")

    try:
        info = extract_video_info(normalized_url)
        return MediaInfoResponse(success=True, **info)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve information for this YouTube video: {str(exc)}"
        )
