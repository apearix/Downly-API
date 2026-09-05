import time
import uuid
import threading
import shutil
import re
from pathlib import Path
from typing import Dict, Optional, Any
from app import config
from app.schemas.job import JobDto, JobProgress
from app.services.ytdlp_service import download_and_merge_media

class JobManager:
    def __init__(self):
        self._jobs: Dict[str, JobDto] = {}
        self._lock = threading.Lock()
        self._start_cleanup_timer()

    def create_job(self, url: str, media_type: str, quality: str) -> JobDto:
        job_id = str(uuid.uuid4())
        job = JobDto(
            id=job_id,
            url=url,
            type=media_type,
            quality=quality,
            status="queued",
            progress=JobProgress(percentage=0.0, phase="Queued for processing"),
            downloadUrl=f"/api/download/{job_id}",
        )
        with self._lock:
            self._jobs[job_id] = job

        # Spawn background processing thread
        thread = threading.Thread(target=self._process_job, args=(job_id,), daemon=True)
        thread.start()
        return job

    def get_job(self, job_id: str) -> Optional[JobDto]:
        with self._lock:
            return self._jobs.get(job_id)

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.pop(job_id, None)

        job_dir = config.STORAGE_DIR / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
        return job is not None

    def _process_job(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return

        with self._lock:
            job.status = "processing"
            job.progress.phase = "Starting download..."

        job_dir = config.STORAGE_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(job_dir / "%(title)s.%(ext)s")

        def progress_hook(d: Dict[str, Any]):
            status = d.get("status")
            with self._lock:
                if status == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes") or 0
                    percent = (downloaded / total * 100) if total > 0 else 0.0
                    job.progress.percentage = round(percent, 1)
                    job.progress.phase = "Downloading media streams..."
                    speed = d.get("speed")
                    if speed:
                        job.progress.speed = f"{speed / (1024*1024):.1f} MB/s"
                    eta = d.get("eta")
                    if eta:
                        job.progress.eta = int(eta)
                elif status == "finished":
                    job.progress.percentage = 95.0
                    job.progress.phase = "Merging video and audio via FFmpeg..."

        try:
            info = download_and_merge_media(
                url=job.url,
                output_path_template=output_template,
                media_type=job.type,
                quality=job.quality,
                progress_hook=progress_hook,
            )

            # Locate the generated file
            files = list(job_dir.glob("*.*"))
            if not files:
                raise FileNotFoundError("Merged file was not created by FFmpeg.")

            result_file = files[0]
            with self._lock:
                job.status = "completed"
                job.filename = result_file.name
                job.progress.percentage = 100.0
                job.progress.phase = "Ready for download"

        except Exception as exc:
            with self._lock:
                job.status = "failed"
                job.error = str(exc)
                job.progress.phase = "Processing failed"

    def _start_cleanup_timer(self):
        def cleanup_loop():
            while True:
                time.sleep(600)  # Check every 10 minutes
                now = time.time()
                for job_dir in config.STORAGE_DIR.glob("*"):
                    try:
                        if job_dir.is_dir() and (now - job_dir.stat().st_mtime > 1800):  # 30 min
                            shutil.rmtree(job_dir, ignore_errors=True)
                    except Exception:
                        pass

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

job_manager = JobManager()
