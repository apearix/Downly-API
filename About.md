# Downly API

Dedicated high-performance media processing backend built with Python, FastAPI, and yt-dlp.

### Architecture Highlights
- **FastAPI Core**: Minimal RAM footprint (~35MB baseline).
- **Native yt-dlp**: In-memory info extraction and stream resolution.
- **bgutil PO Token Provider**: Automated BotGuard PO token injection on port 4416.
- **Render Ready**: Optimized for 512MB RAM free instances with zero OOM crashes.
- **Chunked Streamer**: Direct pipe to browser without saving large files to disk.
