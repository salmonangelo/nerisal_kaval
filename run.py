import time
import cv2
import numpy as np
import requests
import argparse
import base64
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
from app.analytics.zone_flow import ZoneFlowTracker
from app.config import DATABASE_NAME, FRAME_INTERVAL_SECONDS

# Configuration
# Multi-source architecture: Each zone maps to an independent video source
SOURCES = {
    "Zone_A": 0,      # Webcam 0 or video file path
    "Zone_B": 1       # Webcam 1 or second video file path
}

API_UPDATE_URL = "http://127.0.0.1:8000/api/internal/update_frame/"
API_CV_FRAMES_URL = "http://127.0.0.1:8000/api/internal/update_cv_frames"

# Module-level dict for base64-encoded CV analysis frames (importable by main.py)
latest_frames = {
    "tracking_A": "",
    "heatmap_A": "",
    "tracking_B": "",
    "heatmap_B": "",
    "risk_zones": "",
    "density_map": ""
}

def frame_to_base64(frame):
    """Encode frame to base64 JPEG with quality optimization."""
    _, buffer = cv2.imencode(
        '.jpg', frame,
        [cv2.IMWRITE_JPEG_QUALITY, 70]
    )
    return base64.b64encode(
        buffer
    ).decode('utf-8')

# Zone configurations: Each zone is independent, capacity-based
zone_config = ZoneConfig(
    zones=[
        RectZone(name="Zone_A", x1=0, y1=0, x2=1920, y2=1080, capacity=100, source=SOURCES["Zone_A"]),
        RectZone(name="Zone_B", x1=0, y1=0, x2=1920, y2=1080, capacity=100, source=SOURCES["Zone_B"]),
    ]
)

def main(sourceA=None, sourceB=None):
    """
    Multi-source crowd monitoring.
    
    Args:
        sourceA: Source for Zone_A (webcam index or video path). Default: SOURCES["Zone_A"]
        sourceB: Source for Zone_B (webcam index or video path). Default: SOURCES["Zone_B"]
    """
    import os
    
    # Override sources with CLI arguments if provided
    effective_sources = SOURCES.copy()
    if sourceA is not None:
        if sourceA.isdigit():
            effective_sources["Zone_A"] = int(sourceA)
        else:
            effective_sources["Zone_A"] = sourceA
    
    if sourceB is not None:
        if sourceB.isdigit():
            effective_sources["Zone_B"] = int(sourceB)
        else:
            effective_sources["Zone_B"] = sourceB
    
    # Validate and resolve file paths
    def validate_source(source):
        """Check if source is valid file or webcam index."""
        if isinstance(source, int):
            return source  # Webcam index is valid
        
        # Check if it's a file path
        if isinstance(source, str):
            # Try absolute path first
            if os.path.isfile(source):
                return source
            
            # Try relative to data/ subdirectory
            data_path = os.path.join("data", source)
            if os.path.isfile(data_path):
                return data_path
            
            # Try relative to current directory
            if os.path.isfile(source):
                return source
            
            # File not found, warn user
            print(f"⚠️  Warning: File not found '{source}'. Will attempt to open anyway.")
            return source
        
        return source
    
    effective_sources["Zone_A"] = validate_source(effective_sources["Zone_A"])
    effective_sources["Zone_B"] = validate_source(effective_sources["Zone_B"])
    
    # Create independent per-zone objects
    samplers = {}
    trackers = {}
    smoothers = {}
    trend_analyzers = {}
    active_zones = {}  # Track which zones are still active
    
    for zone_name, source in effective_sources.items():
        try:
            sampler = FrameSampler(source, interval=FRAME_INTERVAL_SECONDS)
            # Test the sampler by reading first frame
            test_frame = next(sampler)
            samplers[zone_name] = sampler
            trackers[zone_name] = SimpleTracker(max_distance=100.0)
            smoothers[zone_name] = RollingAverage(window=5)
            trend_analyzers[zone_name] = TrendAnalyzer()
            active_zones[zone_name] = True
            print(f"✓ {zone_name} initialized: {source}")
        except Exception as e:
            print(f"✗ {zone_name} failed to initialize: {source}")
            print(f"  Error: {e}")
            active_zones[zone_name] = False
    
    # Check if any zones are active
    if not any(active_zones.values()):
        print("❌ No zones could be initialized. Check your sources.")
        return
    
    # Shared detectors and processors
    detector = PeopleDetector()
    engine = RiskEngine()
    db = DBManager(DATABASE_NAME)
    alerts = AlertManager()
    
    # Visualizers
    heatmap_gen = HeatmapGenerator()
    tracking_view = TrackingView()
    zone_overlay = ZoneOverlay()
    cluster_det = ClusterDetector()
    zone_mapper = ZoneMapper(zone_config)
    
    # Flow tracking
    flow_tracker = ZoneFlowTracker()
    
    print(f"\n🎬 Starting Multi-Source Detection Loop...")
    print(f"  Zone_A: {effective_sources.get('Zone_A')} {'✓' if active_zones.get('Zone_A') else '✗'}")
    print(f"  Zone_B: {effective_sources.get('Zone_B')} {'✓' if active_zones.get('Zone_B') else '✗'}\n")
    
    try:
        while True:
            # Performance tracking
            loop_start = time.perf_counter()
            latencies = {
                "fetch": 0,
                "detect": 0,
                "process": 0,
                "viz": 0,
                "delivery": 0
            }
            
            zone_metrics_payload = {}
            cv_frames_data = {}
            
            # Step 1: Process each zone independently (skip inactive zones)
            for zone_name, sampler in samplers.items():
                if not active_zones.get(zone_name):
                    continue
                
                try:
                    t0 = time.perf_counter()
                    frame = next(sampler)
                    latencies["fetch"] += (time.perf_counter() - t0)
                except StopIteration:
                    print(f"⚠️  {zone_name} source ended (file completed). Deactivating...")
                    active_zones[zone_name] = False
                    continue
                except Exception as e:
                    print(f"⚠️  {zone_name} source error: {e}. Deactivating...")
                    active_zones[zone_name] = False
                    continue
                
                # Step 1a: Detection
                t0 = time.perf_counter()
                det = detector.detect(frame)
                boxes = det["boxes"]
                latencies["detect"] += (time.perf_counter() - t0)
                
                # Step 1b: Map boxes to zones
                t0 = time.perf_counter()
                zone_mapped = zone_mapper.map_boxes(boxes, frame.shape)
                zone_result = zone_mapped.get(zone_name, {"count": 0, "detections": []})
                
                # Step 1c: Heatmap & Cluster detection
                # Use ALL boxes for global heatmap
                raw_heatmap, colored_heatmap = heatmap_gen.generate_full(boxes, frame.shape)
                zone = [z for z in zone_config.zones if z.name == zone_name][0]
                cluster_res = cluster_det.detect_clusters(raw_heatmap, zone.points, zone.capacity)
                
                # Step 1d: Tracking
                tracked = trackers[zone_name].update(boxes)
                
                # Step 1e: Flow Tracking - Assign tracked objects to zones
                # For simplicity within single-zone loop: all tracked objects belong to current zone
                zone_assignments = {}
                for tracked_obj in tracked:
                    obj_id = tracked_obj["id"]
                    zone_assignments[obj_id] = zone_name
                
                # Update flow tracker
                flow_tracker.update(tracked, zone_assignments)
                
                # Step 1f: Density calculation (using zone_mapper result)
                count = zone_result["count"]
                raw_density = count / zone.capacity if zone.capacity > 0 else 0
                smoothed_density = smoothers[zone_name].update(zone_name, raw_density)
                latencies["process"] += (time.perf_counter() - t0)
                
                # Store metrics
                zone_metrics_payload[zone_name] = {
                    "count": count,
                    "capacity": zone.capacity,
                    "density": smoothed_density,
                    "local_density": zone_result.get("local_density", 0),
                    "cluster_res": cluster_res,
                    "frame": frame,
                    "boxes": boxes,
                    "heatmap": raw_heatmap,
                    "colored_heatmap": colored_heatmap
                }
            
            # Check if all zones are dead
            if not any(active_zones.values()):
                print("❌ All zones disconnected. Exiting...")
                break
            
            if not zone_metrics_payload:
                continue
            
            # Step 2: Risk Assessment (per zone)
            t0 = time.perf_counter()
            densities = {z: m["density"] for z, m in zone_metrics_payload.items()}
            local_ds = {z: 0 for z in zone_metrics_payload.keys()}
            counts = {z: m["count"] for z, m in zone_metrics_payload.items()}
            caps = {z: m["capacity"] for z, m in zone_metrics_payload.items()}
            
            # Add density to trend for each zone
            for zone_name, density in densities.items():
                trend_analyzers[zone_name].add_density({zone_name: density})
            
            # Get growth rates
            growth_rates = {}
            for zone_name, trend in trend_analyzers.items():
                gr = trend.growth_rate()
                growth_rates[zone_name] = gr.get(zone_name, 0)
            
            # Assess risk
            cluster_data = {z: m["cluster_res"] for z, m in zone_metrics_payload.items()}
            assessed = engine.assess(densities, local_ds, counts, caps, growth_rates, cluster_data)
            latencies["process"] += (time.perf_counter() - t0)
            
            # Step 3: Visualization & Streaming
            t0 = time.perf_counter()
            all_zones_for_overlay = {z.name: z.points for z in zone_config.zones}
            
            for zone_name, metrics in zone_metrics_payload.items():
                frame = metrics["frame"]
                data = assessed[zone_name]
                risk_level = data.get("risk_level", "Green")
                
                frame_h, frame_w = frame.shape[:2]
                
                t_view = tracking_view.draw(frame.copy(), metrics["boxes"], risk_level)
                
                # Use pre-generated colored heatmap
                h_view = metrics["colored_heatmap"]
                
                z_view = zone_overlay.draw(frame.copy(), {zone_name: all_zones_for_overlay[zone_name]}, assessed)
                
                # Capture screenshot once (optional for portfolio)
                if not hasattr(main, 'screenshot_taken'):
                    cv2.imwrite("screenshot_viz.jpg", z_view)
                    cv2.imwrite("screenshot_tracking.jpg", t_view)
                    cv2.imwrite("screenshot_heatmap.jpg", h_view)
                    main.screenshot_taken = True
                    print("📸 Portfolio screenshots saved to root directory.")

                # Encode to base64
                zone_letter = zone_name.split('_')[1]
                tracking_key = f"tracking_{zone_letter}"
                heatmap_key = f"heatmap_{zone_letter}"
                
                latest_frames[tracking_key] = frame_to_base64(t_view)
                latest_frames[heatmap_key] = frame_to_base64(h_view)
                cv_frames_data[tracking_key] = latest_frames[tracking_key]
                cv_frames_data[heatmap_key] = latest_frames[heatmap_key]
                latest_frames["risk_zones"] = frame_to_base64(z_view)
                cv_frames_data["risk_zones"] = latest_frames["risk_zones"]
                
                # Dedicated density map for standalone heatmap section
                latest_frames["density_map"] = latest_frames[heatmap_key]
                cv_frames_data["density_map"] = latest_frames["density_map"]
                
                # MJPEG stream
                _, buffer = cv2.imencode('.jpg', z_view)
                try:
                    requests.post(f"{API_UPDATE_URL}{zone_name}", data=buffer.tobytes(), timeout=0.2)
                except:
                    pass
            latencies["viz"] += (time.perf_counter() - t0)
            
            # Step 4: Send CV frames + flows to API
            t0 = time.perf_counter()
            
            # Add zone flows to the payload
            flows_data = flow_tracker.get_flows_formatted()
            cv_frames_data["zone_flows"] = flows_data
            
            try:
                requests.post(API_CV_FRAMES_URL, json=cv_frames_data, timeout=0.5)
            except:
                pass
            latencies["delivery"] += (time.perf_counter() - t0)
            
            # Step 5: Database persistence & alerts
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
            
            loop_end = time.perf_counter()
            total_time = loop_end - loop_start
            fps = 1.0 / total_time if total_time > 0 else 0
            
            active_status = "  ".join([f"{z}:{'✓' if active_zones[z] else '✗'}" for z in active_zones])
            perf_str = f"FPS: {fps:.1f} | Latency: {total_time*1000:.1f}ms (Det: {latencies['detect']*1000:.1f}ms, Proc: {latencies['process']*1000:.1f}ms, Viz: {latencies['viz']*1000:.1f}ms)"
            print(f"[{time.strftime('%H:%M:%S')}] {perf_str} | {active_status}")
            
            # Fixed interval sleep (adjust for real-time simulation)
            sleep_time = max(0, FRAME_INTERVAL_SECONDS - total_time)
            time.sleep(sleep_time)


    except KeyboardInterrupt:
        print("\n⏹️  Stopping loop...")
    finally:
        for sampler in samplers.values():
            sampler.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sourceA",
        default=None,
        help="Source for Zone_A (webcam index 0-9 or video file path)"
    )
    parser.add_argument(
        "--sourceB",
        default=None,
        help="Source for Zone_B (webcam index 0-9 or video file path)"
    )
    args = parser.parse_args()

    main(sourceA=args.sourceA, sourceB=args.sourceB)
