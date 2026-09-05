import httpx
from typing import AsyncGenerator, Dict, Any
from fastapi.responses import StreamingResponse
from urllib.parse import quote

CHUNK_SIZE = 64 * 1024  # 64 KB chunks

async def generate_chunks(url: str, headers: Dict[str, str]) -> AsyncGenerator[bytes, None]:
    """
    Streams bytes directly from the media source with backpressure.
    """
    req_headers = {k: v for k, v in headers.items() if k.lower() != "host"}

    async with httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(60.0, read=None)) as client:
        async with client.stream("GET", url, headers=req_headers) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                if chunk:
                    yield chunk

def create_streaming_response(stream_details: Dict[str, Any]) -> StreamingResponse:
    """
    Creates a FastAPI StreamingResponse matching Next.js download headers.
    """
    direct_url = stream_details["direct_url"]
    filename = stream_details["filename"]
    filesize = stream_details["filesize"]
    headers = stream_details["headers"]
    mime_type = stream_details["mime_type"]

    safe_ascii_filename = "".join(c for c in filename if 32 <= ord(c) <= 126 and c not in '"\\')
    encoded_filename = quote(filename)

    resp_headers = {
        "Content-Disposition": f'attachment; filename="{safe_ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}',
        "X-Filename": encoded_filename,
        "Access-Control-Expose-Headers": "Content-Disposition, Content-Length, X-Filename",
    }

    if filesize and filesize > 0:
        resp_headers["Content-Length"] = str(filesize)

    return StreamingResponse(
        generate_chunks(direct_url, headers),
        media_type=mime_type,
        headers=resp_headers,
    )
