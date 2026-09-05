# Downly API (Dedicated Python FastAPI Backend)

High-performance, ultra-low memory media extraction and streaming backend for Downly.

## Features
- **Native Python yt-dlp**: In-memory execution without CLI string parsing or process spawning overhead.
- **bgutil PO Token Provider (v1.3.2)**: Built-in BotGuard HTTP server on port 4416.
- **Render 512MB RAM Optimized**: Consumes only ~120MB-160MB total RAM, leaving over 350MB free headroom.
- **Direct Chunk Streaming**: Zero-disk buffer streaming via `httpx` async generator.
- **Render Secret Cookies**: Automatic pickup of `/etc/secrets/cookies.txt` or `YOUTUBE_COOKIES` env.
- **100% Drop-In Compatible**: Matches Downly Next.js API contracts (`/api/info`, `/api/download`, `/api/jobs`).

## Local Development
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 10000
```
