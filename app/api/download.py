import os
from urllib.parse import quote
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from app import config
from app.schemas.download import DownloadRequest
from app.core.url import validate_and_normalize_youtube_url
from app.services.ytdlp_service import get_direct_stream_details
from app.services.stream_service import create_streaming_response
from app.services.job_service import job_manager

router = APIRouter(prefix="/api", tags=["download"])

@router.post("/download")
async def download_media_post(payload: DownloadRequest):
    is_valid, normalized_url, error = validate_and_normalize_youtube_url(payload.url)
    if not is_valid or not normalized_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid YouTube URL.")

    media_type = payload.type or "video"
    quality = payload.quality or "1080p"

    try:
        stream_details = get_direct_stream_details(normalized_url, media_type, quality)
        if not stream_details.get("direct_url"):
            raise ValueError("Direct stream URL could not be resolved.")
        return create_streaming_response(stream_details)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to download this media: {str(exc)}"
        )

@router.get("/download")
async def download_media_get(
    url: str = Query(..., description="YouTube URL"),
    type: str = Query("video", description="video or audio"),
    quality: str = Query("1080p", description="Requested quality (e.g. 720p, 1080p)")
):
    is_valid, normalized_url, error = validate_and_normalize_youtube_url(url)
    if not is_valid or not normalized_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid YouTube URL.")

    try:
        stream_details = get_direct_stream_details(normalized_url, type, quality)
        if not stream_details.get("direct_url"):
            raise ValueError("Direct stream URL could not be resolved.")
        return create_streaming_response(stream_details)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to download this media: {str(exc)}"
        )

@router.get("/download/{job_id}")
async def download_job_file(job_id: str):
    job = job_manager.get_job(job_id)
    if not job or job.status != "completed" or not job.filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File is not ready, has expired, or does not exist."
        )

    file_path = config.STORAGE_DIR / job_id / job.filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file is no longer available."
        )

    mime_type = "audio/mpeg" if job.type == "audio" else "video/mp4"
    safe_filename = "".join(c for c in job.filename if 32 <= ord(c) <= 126 and c not in '"\\')
    encoded_filename = quote(job.filename)

    headers = {
        "Content-Disposition": f'attachment; filename="{safe_filename}"; filename*=UTF-8\'\'{encoded_filename}',
        "X-Filename": encoded_filename,
        "Access-Control-Expose-Headers": "Content-Disposition, Content-Length, X-Filename",
    }

    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=safe_filename,
        headers=headers,
    )
