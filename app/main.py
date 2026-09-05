import yt_dlp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import config
from app.api.info import router as info_router
from app.api.download import router as download_router
from app.api.jobs import router as jobs_router

app = FastAPI(
    title="Downly API",
    description="High-performance media extraction and streaming service",
    version="1.0.0"
)

# CORS Middleware to allow Next.js frontend (Vercel) to interact with Downly API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length", "X-Filename"],
)

# Register API Routers
app.include_router(info_router)
app.include_router(download_router)
app.include_router(jobs_router)

@app.get("/")
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "downly-api",
        "version": "1.0.0",
        "ytdlp_version": getattr(yt_dlp.version, "__version__", "unknown"),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=config.PORT, reload=False)
