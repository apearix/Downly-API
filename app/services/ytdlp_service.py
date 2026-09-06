import re
import os
from typing import Dict, Any, List, Optional, Callable
import yt_dlp
from app import config

def parse_quality_to_height(quality: Optional[str]) -> int:
    if not quality:
        return 1080
    match = re.search(r'(\d+)', quality)
    if match:
        val = int(match.group(1))
        if val > 0:
            return val
    q_lower = quality.lower()
    if "4k" in q_lower:
        return 2160
    if "2k" in q_lower:
        return 1440
    return 1080

def get_base_ydl_opts(extra_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cookies_path = config.get_cookies_path()
    # mweb and web are supported by bgutil PO token provider and yield full 1080p+ formats
    client_list = ["mweb", "web", "default"]

    opts: Dict[str, Any] = {
        "noplaylist": True,
        "source_address": "0.0.0.0",  # force IPv4
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "remote_components": ["ejs:github"],
        "js_runtimes": {"deno": {}, "node": {}},
        "extractor_args": {
            "youtube": {
                "player_client": client_list,
            },
            "youtubepot-bgutilhttp": {
                "base_url": [config.BGUTIL_URL],
            },
            "youtubepot-bgutilscript": {
                "disabled": ["true"],
            },
        },
    }

    if cookies_path and os.path.exists(cookies_path):
        opts["cookiefile"] = cookies_path

    if config.FFMPEG_LOCATION:
        opts["ffmpeg_location"] = config.FFMPEG_LOCATION

    if extra_opts:
        opts.update(extra_opts)

    return opts

def extract_video_info(url: str) -> Dict[str, Any]:
    """
    Extracts video metadata and resolves available qualities.
    """
    opts = get_base_ydl_opts({
        "skip_download": True,
        "dump_single_json": True,
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("No video metadata returned from YouTube.")

    formats = info.get("formats", [])
    has_formats = len(formats) > 0

    available_heights = set()
    for f in formats:
        h = f.get("height")
        if h and isinstance(h, int) and h > 0:
            available_heights.add(h)

    qualities = []
    if available_heights:
        for standard in config.STANDARD_RESOLUTIONS:
            if any(h >= standard["height"] for h in available_heights):
                qualities.append(standard)
    elif has_formats:
        qualities = [
            {"height": 360, "id": "360p", "label": "360p"},
            {"height": 720, "id": "720p", "label": "720p HD"},
            {"height": 1080, "id": "1080p", "label": "1080p FHD"},
        ]
    else:
        qualities = [{"height": 720, "id": "720p", "label": "720p HD"}]

    unique_qualities = []
    seen = set()
    for q in reversed(qualities):
        if q["id"] not in seen:
            seen.add(q["id"])
            unique_qualities.append(q)

    return {
        "title": info.get("title", "YouTube Video"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "channel": info.get("uploader") or info.get("channel"),
        "qualities": unique_qualities,
    }

def get_direct_stream_details(url: str, media_type: str = "video", quality: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts direct playable stream URL for progressive or audio formats.
    """
    is_audio = media_type == "audio"
    target_height = parse_quality_to_height(quality)

    if is_audio:
        fmt_spec = "bestaudio/best"
    else:
        fmt_spec = f"best[height<={target_height}][ext=mp4]/best[height<={target_height}]/best"

    opts = get_base_ydl_opts({
        "format": fmt_spec,
        "skip_download": True,
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Unable to extract stream info.")

    title = info.get("title", "media")
    ext = "mp3" if is_audio else (info.get("ext") or "mp4")
    raw_filename = f"{title}.{ext}"

    safe_filename = re.sub(r'[^\w\s.-]', '_', raw_filename).strip()
    direct_url = info.get("url")
    filesize = info.get("filesize") or info.get("filesize_approx") or 0
    http_headers = info.get("http_headers") or {}

    return {
        "direct_url": direct_url,
        "filename": safe_filename,
        "filesize": filesize,
        "headers": http_headers,
        "mime_type": "audio/mpeg" if is_audio else f"video/{ext}",
    }

def download_and_merge_media(
    url: str,
    output_path_template: str,
    media_type: str = "video",
    quality: Optional[str] = None,
    progress_hook: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Downloads and merges media into a local temporary file using FFmpeg.
    """
    is_audio = media_type == "audio"
    target_height = parse_quality_to_height(quality)

    if is_audio:
        fmt_spec = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        fmt_spec = f"bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]/best"
        postprocessors = [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }]

    opts = get_base_ydl_opts({
        "format": fmt_spec,
        "outtmpl": output_path_template,
        "postprocessors": postprocessors,
        "merge_output_format": "mp4" if not is_audio else None,
    })

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info
