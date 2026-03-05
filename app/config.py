# global configuration constants for CrowdCare

FRAME_INTERVAL_SECONDS: float = 5.0
YOLO_MODEL_NAME: str = "yolov8n.pt"
DATABASE_NAME: str = "metrics.db"

# risk configuration
RISK_THRESHOLDS = {
    "green": 0.6,
    "amber": 0.85,
}

RISK_WEIGHTS = {
    "density": 0.7,
    "growth": 0.3,
}

# note: connectivity config or callbacks may be added here later
