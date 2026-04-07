import time
import cv2
import numpy as np
import requests
import argparse
from app.capture.frame_sampler import FrameSampler
from app.detection.people_detector import PeopleDetector
from app.tracking.tracker import SimpleTracker
from app.density.grid_density import compute_grid_density
from app.utils.smoother import RollingAverage
from app.detection.density_classifier import get_density_label
from app.zones.zone_config import RectZone, ZoneConfig
from app.zones.zone_mapper import ZoneMapper
from app.risk.risk_engine import RiskEngine
from app.risk.trend_analyzer import TrendAnalyzer
from app.database.db_manager import DBManager
from app.alerts.alert_manager import AlertManager
from app.visualization.heatmap_generator import HeatmapGenerator
from app.visualization.tracking_view import TrackingView
from app.visualization.zone_overlay import ZoneOverlay
from app.zones.cluster_detector import ClusterDetector
from app.config import DATABASE_NAME, FRAME_INTERVAL_SECONDS

# Configuration
# Map zones to camera indices. Multiple zones can share the same source.
SOURCES_MAP = {
    "Zone_A": 0,
    "Zone_B": 0  # Re-using 0 for testing if only one cam is available
}

API_UPDATE_URL = "http://127.0.0.1:8000/api/internal/update_frame/"

zone_config = ZoneConfig(
    zones=[
        RectZone(name="Zone_A", x1=0, y1=0, x2=320, y2=480, capacity=50, source=SOURCES_MAP["Zone_A"]),
        RectZone(name="Zone_B", x1=320, y1=0, x2=640, y2=480, capacity=75, source=SOURCES_MAP["Zone_B"]),
    ]
)



def main(source=None):
    # Store samplers by unique source index to avoid hardware locks
    # Use CLI source if provided, otherwise default to SOURCES_MAP
    if source is not None:
        effective_sources = {z: source for z in SOURCES_MAP}
    else:
        effective_sources = SOURCES_MAP

    unique_sources = set(effective_sources.values())
    samplers = {src: FrameSampler(src, interval=FRAME_INTERVAL_SECONDS) for src in unique_sources}
    
    # Trackers and smoothers remain per-zone
    trackers = {z.name: SimpleTracker(max_distance=100.0) for z in zone_config.zones}
    smoothers = {z.name: RollingAverage(window=5) for z in zone_config.zones}

    detector = PeopleDetector()
    mapper = ZoneMapper(zone_config)
    engine = RiskEngine()
    trend = TrendAnalyzer()
    db = DBManager(DATABASE_NAME)
    alerts = AlertManager()
    
    # Visualizers and Detectors
    heatmap_gen = HeatmapGenerator()
    tracking_view = TrackingView()
    zone_overlay = ZoneOverlay()
    cluster_det = ClusterDetector()

    print(f"Starting Multi-Camera Detection Loop with {len(samplers)} unique sources...")
    
    try:
        while True:
            zone_metrics_payload = {}
            
            # Step 1: Capture frames for each unique physical camera
            source_frames = {}
            for src_id, sampler in samplers.items():
                try:
                    source_frames[src_id] = next(sampler)
                except StopIteration:
                    print(f"Source {src_id} disconnected.")
                    continue

            # Step 2: Process each logical zone using its mapped source frame
            for zone in zone_config.zones:
                zone_name = zone.name
                src_id = effective_sources.get(zone_name)
                
                if src_id not in source_frames:
                    continue
                
                frame = source_frames[src_id].copy() # copy to avoid drawing overlap between zones
                
                # Detection (Ideally we'd also share detection per frame, but trackers need independent boxes)
                det = detector.detect(frame)
                boxes = det["boxes"]
                
                # 1. New Detectors
                heatmap = heatmap_gen.generate(boxes, frame.shape)
                cluster_res = cluster_det.detect_clusters(heatmap, zone.points, zone.capacity)
                
                # Independent tracking per zone
                tracked = trackers[zone_name].update(boxes)
                tracked_boxes = [t["bbox"] for t in tracked]
                
                # Metrics
                mapped_stats = mapper.map_boxes(tracked_boxes, frame_shape=frame.shape)
                z_info = mapped_stats.get(zone_name, {"count": 0, "capacity": 1, "local_density": 0})
                
                raw_density = z_info["count"] / z_info["capacity"]
                smoothed_density = smoothers[zone_name].update(zone_name, raw_density)
                
                zone_metrics_payload[zone_name] = {
                    "count": z_info["count"],
                    "capacity": z_info["capacity"],
                    "density": smoothed_density,
                    "local_density": z_info["local_density"],
                    "cluster_res": cluster_res,
                    "frame": frame,
                    "boxes": boxes,
                    "heatmap": heatmap
                }

            if not zone_metrics_payload:
                continue

            # Step 3: Global Risk Assessment & Database Persistence
            densities = {z: m["density"] for z, m in zone_metrics_payload.items()}
            local_ds = {z: m["local_density"] for z, m in zone_metrics_payload.items()}
            counts = {z: m["count"] for z, m in zone_metrics_payload.items()}
            caps = {z: m["capacity"] for z, m in zone_metrics_payload.items()}
            
            trend.add_density(densities)
            cluster_data = {z: m["cluster_res"] for z, m in zone_metrics_payload.items()}
            assessed = engine.assess(densities, local_ds, counts, caps, trend.growth_rate(), cluster_data)

            # Step 4: Visualization and Streaming
            for zone_name, metrics in zone_metrics_payload.items():
                frame = metrics["frame"]
                data = assessed[zone_name]
                
                # 1. Generate specialized views
                t_view = tracking_view.draw(frame, metrics["boxes"])
                h_overlay = heatmap_gen.to_overlay(metrics["heatmap"])
                # Blend BGR with heatmap RGB (ignoring alpha channel for standard imshow blend)
                h_view = cv2.addWeighted(frame, 0.6, h_overlay[:, :, :3], 0.4, 0)
                z_view = zone_overlay.draw(frame, {z.name: z.points for z in zone_config.zones}, assessed)
                
                try:
                    cv2.imshow(f"Tracking - {zone_name}", t_view)
                    cv2.imshow(f"Heatmap - {zone_name}", h_view)
                    cv2.imshow(f"Risk Zones", z_view)
                    cv2.waitKey(1)
                except:
                    pass

                # MJPEG stream (use z_view for dashboard)
                _, buffer = cv2.imencode('.jpg', z_view)
                try:
                    requests.post(f"{API_UPDATE_URL}{zone_name}", data=buffer.tobytes(), timeout=0.2)
                except:
                    pass

            # Step 5: Database Persistence
            for zone, data in assessed.items():
                db.insert_metric(
                    zone,
                    data["count"],
                    data["density"],
                    data["risk_level"],
                    local_density=data["local_density"],
                    density_class=data["density_class"],
                    cluster_detected=data["cluster_detected"],
                    cluster_risk=data["cluster_risk"],
                    hotspot_x=data["hotspot_center"][0],
                    hotspot_y=data["hotspot_center"][1],
                    cluster_ratio=data["cluster_ratio"]
                )
                
            _ = alerts.check({z: {
                "risk_level": d["risk_level"],
                "cluster_detected": d["cluster_detected"]
            } for z, d in assessed.items()})
            print(f"Processed: {list(zone_metrics_payload.keys())}")
            
            time.sleep(FRAME_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("Stopping loop...")
    finally:
        for s in samplers.values(): s.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=None,
        help="Webcam index (0,1,...) or video file path"
    )
    args = parser.parse_args()

    source = args.source
    if source is not None and source.isdigit():
        source = int(source)

    main(source=source)
