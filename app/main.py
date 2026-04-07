import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import DATABASE_NAME
from .database.db_manager import DBManager
from typing import List, Dict, Any

@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize a database manager on startup
    app.state.db = DBManager(f"{DATABASE_NAME}")
    yield

app = FastAPI(title="CrowdCare API", lifespan=lifespan)

# Global in-memory buffer for live frames
latest_frames: Dict[str, bytes] = {}

# Enable CORS for dashboard to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Internal endpoint for run.py to push processed frames
@app.post("/api/internal/update_frame/{zone}")
async def update_frame(zone: str, frame: bytes = Body(...)):
    latest_frames[zone] = frame
    return {"status": "ok"}


@app.get("/api/stream/{zone}")
async def stream_zone(zone: str):
    """MJPEG streaming endpoint for a specific zone."""
    async def frame_generator():
        while True:
            if zone in latest_frames:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frames[zone] + b'\r\n')
            await asyncio.sleep(0.1) # Controls stream FPS (approx 10 FPS)
            
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


# API routes must be defined BEFORE static files mount to take priority
@app.get("/api/status")
def get_status():
    """Get latest status for all zones."""
    db: DBManager = app.state.db
    status = db.get_latest_status()
    # ensure we return a list even if empty
    return status if status else []


@app.get("/api/history/{zone}")
def get_history(zone: str):
    """Get zone history."""
    db: DBManager = app.state.db
    history = db.get_zone_history(zone)
    if not history:
        return []  # return empty list instead of 404
    return history


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "CrowdCare API is running"}


# Serve static dashboard files at root - mounted AFTER API routes so they take priority
app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
