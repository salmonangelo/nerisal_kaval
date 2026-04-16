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

# Global in-memory buffer for live frames (MJPEG streams)
latest_frames_mjpeg: Dict[str, bytes] = {}

# Global zone flow data
latest_flows: List[Dict[str, Any]] = []

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
    latest_frames_mjpeg[zone] = frame
    return {"status": "ok"}


@app.post("/api/internal/update_cv_frames")
async def update_cv_frames(frames_data: Dict[str, Any] = Body(...)):
    """Receive base64-encoded CV analysis frames and zone flow data from run.py."""
    global latest_flows
    
    # Lazy import to avoid circular dependency
    from run import latest_frames
    
    # Extract flows if present
    if "zone_flows" in frames_data:
        latest_flows = frames_data.pop("zone_flows")
    
    # Update frames (remove zone_flows before storing in latest_frames)
    latest_frames.update(frames_data)
    return {"status": "ok"}


# CV Analysis Frames API Endpoints
@app.get("/api/frames")
def get_all_frames():
    """Get all base64-encoded CV analysis frames."""
    # Lazy import to avoid circular dependency
    from run import latest_frames
    return latest_frames


@app.get("/api/frames/{frame_name}")
def get_single_frame(frame_name: str):
    """Get a single base64-encoded CV analysis frame.
    
    Valid frame names: tracking_A, tracking_B, heatmap_A, heatmap_B, risk_zones, density_map
    """
    # Lazy import to avoid circular dependency
    from run import latest_frames
    if frame_name not in latest_frames:
        return {"error": f"Frame '{frame_name}' not found", "available": list(latest_frames.keys())}
    return {"frame_name": frame_name, "data": latest_frames[frame_name]}


@app.get("/api/flows")
def get_flows():
    """Get zone-to-zone flow data (people movement between zones).
    
    Returns:
        List of flow records: [{"from": "Zone_A", "to": "Zone_B", "count": 12}, ...]
    """
    global latest_flows
    return latest_flows


@app.get("/api/heatmap")
def get_heatmap():
    """Returns the latest density heatmap as a JPEG image."""
    import base64
    from fastapi import Response
    # Lazy import to avoid circular dependency
    from run import latest_frames
    
    data = latest_frames.get("density_map", "")
    if not data:
        return Response(status_code=204) # No Content
        
    try:
        img_bytes = base64.b64decode(data)
        return Response(content=img_bytes, media_type="image/jpeg")
    except Exception as e:
        return {"error": f"Failed to decode image: {e}"}


@app.get("/api/stream/{zone}")
async def stream_zone(zone: str):
    """MJPEG streaming endpoint for a specific zone."""
    async def frame_generator():
        while True:
            if zone in latest_frames_mjpeg:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frames_mjpeg[zone] + b'\r\n')
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
