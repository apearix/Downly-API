import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

# Server & Network Config
PORT: int = int(os.getenv("PORT", "10000"))
BGUTIL_PORT: int = int(os.getenv("BGUTIL_PORT", "4416"))
BGUTIL_URL: str = os.getenv("BGUTIL_URL", f"http://127.0.0.1:{BGUTIL_PORT}")
FFMPEG_LOCATION: Optional[str] = os.getenv("FFMPEG_LOCATION", os.getenv("FFMPEG_PATH", None))

# Local temporary storage for merged media
STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", "/tmp/downly-storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Standard YouTube Resolutions
STANDARD_RESOLUTIONS: List[Dict[str, Any]] = [
    {"height": 144, "id": "144p", "label": "144p"},
    {"height": 240, "id": "240p", "label": "240p"},
    {"height": 360, "id": "360p", "label": "360p"},
    {"height": 480, "id": "480p", "label": "480p"},
    {"height": 720, "id": "720p", "label": "720p HD"},
    {"height": 1080, "id": "1080p", "label": "1080p FHD"},
    {"height": 1440, "id": "1440p", "label": "1440p 2K"},
    {"height": 2160, "id": "2160p", "label": "2160p 4K"},
]

def get_cookies_path() -> Optional[str]:
    """
    Detects and prepares the cookies file.
    Copies read-only Render secret (/etc/secrets/cookies.txt) to writable /tmp
    to prevent yt-dlp cookie-save errors.
    """
    tmp_cookies = Path("/tmp/youtube-cookies.txt")
    render_secret = Path("/etc/secrets/cookies.txt")

    if render_secret.exists():
        try:
            shutil.copyfile(render_secret, tmp_cookies)
            return str(tmp_cookies)
        except Exception:
            return str(render_secret)

    env_cookies = os.getenv("YOUTUBE_COOKIES")
    if env_cookies:
        try:
            content = env_cookies.strip()
            if content.startswith("base64:"):
                import base64
                content = base64.b64decode(content[7:]).decode("utf-8")
            elif "\\n" in content and "\n" not in content:
                content = content.replace("\\n", "\n")
            tmp_cookies.write_text(content, encoding="utf-8")
            return str(tmp_cookies)
        except Exception:
            pass

    local_cookies = Path("./cookies.txt")
    if local_cookies.exists():
        return str(local_cookies.resolve())

    return None
