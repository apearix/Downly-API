import re
from urllib.parse import urlparse
from typing import Tuple, Optional

YOUTUBE_REGEX = re.compile(
    r'^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?.*v=|shorts/|embed/)|youtu\.be/)([\w-]{11})',
    re.IGNORECASE
)

def validate_and_normalize_youtube_url(raw_url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates YouTube URL and returns (is_valid, normalized_url, error_message).
    """
    if not raw_url or not isinstance(raw_url, str):
        return False, None, "Please provide a valid URL."

    url = raw_url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        urlparse(url)
    except Exception:
        return False, None, "Malformed URL format."

    match = YOUTUBE_REGEX.match(url)
    if not match:
        return False, None, "Please provide a valid YouTube video or shorts URL."

    video_id = match.group(5)
    normalized = f"https://www.youtube.com/watch?v={video_id}"
    return True, normalized, None
