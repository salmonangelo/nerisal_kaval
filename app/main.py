from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import DATABASE_NAME
from .database.db_manager import DBManager
from typing import List, Dict, Any

app = FastAPI(title="CrowdCare API")

# Enable CORS for dashboard to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize a database manager on startup
@app.on_event("startup")
def startup_event():
    app.state.db = DBManager(f"{DATABASE_NAME}")


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
