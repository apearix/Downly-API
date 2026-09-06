from fastapi import APIRouter, HTTPException, status
from app.schemas.job import JobCreateRequest, JobCreateResponse, JobStatusResponse
from app.core.url import validate_and_normalize_youtube_url
from app.services.job_service import job_manager

router = APIRouter(prefix="/api", tags=["jobs"])

@router.post("/jobs", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_download_job(payload: JobCreateRequest):
    is_valid, normalized_url, error = validate_and_normalize_youtube_url(payload.url)
    if not is_valid or not normalized_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid YouTube URL.")

    media_type = payload.type or "video"
    quality = payload.quality or "1080p"

    job = job_manager.create_job(
        url=normalized_url,
        media_type=media_type,
        quality=quality,
    )

    return JobCreateResponse(success=True, jobId=job.id, job=job)

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or expired."
        )

    return JobStatusResponse(success=True, job=job)

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    deleted = job_manager.delete_job(job_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found."
        )
    return {"success": True, "message": "Job cancelled and deleted."}
