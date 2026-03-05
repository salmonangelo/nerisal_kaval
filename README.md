# CrowdCare (Nerisal Kaval)

Modular AI-powered crowd risk monitoring system.

## Components

- **app/**: Backend modules and logic
- **dashboard/**: Simple front-end to display metrics
- **run.py**: Standalone detection loop

## Requirements

- Python 3.10+
- FastAPI, Ultralytics YOLOv8, OpenCV, Shapely, SQLite

## Running

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start backend API:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Run the detection loop (in separate terminal):
   ```bash
   python run.py
   ```
4. Access dashboard at http://localhost:8000/dashboard/index.html (serve via static server or open file)

## Note

This project uses in-memory zone definitions and an SQLite database. It is designed for modular testing and integration. Images are not stored.
