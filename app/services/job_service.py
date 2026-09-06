import time
import uuid
import threading
import shutil
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
        now = int(time.time() * 1000)
        job = JobDto(
            id=job_id,
            url=url,
            type=media_type,
            quality=quality,
            status="queued",
            progress=JobProgress(percentage=0.0, phase="Queued for processing"),
            downloadUrl=None,
            outputFormat="mp3" if media_type == "audio" else "mp4",
            createdAt=now,
            updatedAt=now,
            expiresAt=now + 1800000,
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
            job.updatedAt = int(time.time() * 1000)

        job_dir = config.STORAGE_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(job_dir / "%(title)s.%(ext)s")

        def progress_hook(d: Dict[str, Any]):
            status = d.get("status")
            with self._lock:
                job.updatedAt = int(time.time() * 1000)
                if status == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes") or 0
                    percent = (downloaded / total * 100) if total > 0 else 0.0
                    job.progress.percentage = round(percent, 1)
                    job.progress.downloadedBytes = downloaded
                    job.progress.totalBytes = total
                    job.progress.phase = "Downloading media streams..."
                    speed = d.get("speed")
                    if speed:
                        job.progress.speed = f"{speed / (1024*1024):.1f} MB/s"
                    eta = d.get("eta")
                    if eta:
                        job.progress.eta = f"{int(eta)}s"
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

            # Locate the generated output file
            all_files = [f for f in job_dir.glob("*.*") if not f.name.endswith(".part")]
            if not all_files:
                raise FileNotFoundError("Merged file was not created by FFmpeg.")

            if job.type == "audio":
                audio_files = [f for f in all_files if f.suffix.lower() == ".mp3"]
                result_file = audio_files[0] if audio_files else all_files[0]
            else:
                video_files = [f for f in all_files if f.suffix.lower() == ".mp4"]
                result_file = video_files[0] if video_files else all_files[0]

            with self._lock:
                job.status = "completed"
                job.filename = result_file.name
                job.fileSize = result_file.stat().st_size
                job.outputFormat = "mp3" if job.type == "audio" else "mp4"
                job.downloadUrl = f"/api/download/{job_id}"
                job.progress.percentage = 100.0
                job.progress.phase = "Ready for download"
                job.updatedAt = int(time.time() * 1000)

        except Exception as exc:
            with self._lock:
                job.status = "failed"
                job.error = str(exc)
                job.progress.phase = "Processing failed"
                job.updatedAt = int(time.time() * 1000)

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
