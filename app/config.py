# global configuration constants for CrowdCare

FRAME_INTERVAL_SECONDS: float = 1.0
YOLO_MODEL_NAME: str = "best.pt"
DATABASE_NAME: str = "metrics.db"

# risk configuration
RISK_THRESHOLDS = {
    "green": 0.3,
    "amber": 0.5,
    "red": 0.7,
}

RISK_WEIGHTS = {
    "density": 0.7,
    "growth": 0.3,
}

# note: connectivity config or callbacks may be added here later
