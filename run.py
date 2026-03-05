import time
from app.capture.frame_sampler import FrameSampler
from app.detection.people_detector import PeopleDetector
from app.zones.zone_config import RectZone, ZoneConfig
from app.zones.zone_mapper import ZoneMapper
from app.risk.risk_engine import RiskEngine
from app.risk.trend_analyzer import TrendAnalyzer
from app.database.db_manager import DBManager
from app.alerts.alert_manager import AlertManager
from app.config import DATABASE_NAME, FRAME_INTERVAL_SECONDS


# sample zone definitions (could be loaded from file)
zone_config = ZoneConfig(
    zones=[
        RectZone(name="Zone_A", x1=0, y1=0, x2=500, y2=500, capacity=50),
        RectZone(name="Zone_B", x1=500, y1=0, x2=1000, y2=500, capacity=75),
        RectZone(name="Zone_C", x1=0, y1=500, x2=500, y2=1000, capacity=100),
    ]
)


def main(source=0):
    sampler = FrameSampler(source, interval=FRAME_INTERVAL_SECONDS)
    detector = PeopleDetector()
    mapper = ZoneMapper(zone_config)
    engine = RiskEngine()
    trend = TrendAnalyzer()
    db = DBManager(f"{DATABASE_NAME}")
    alerts = AlertManager()

    try:
        for frame in sampler:
            # detection
            det = detector.detect(frame)
            boxes = det["boxes"]

            # mapping
            zone_stats = mapper.map_boxes(boxes)
            counts = {z: info["count"] for z, info in zone_stats.items()}
            capacities = {z: info.get("capacity") for z, info in zone_stats.items()}

            # growth/trend
            densities = {}
            for z, info in zone_stats.items():
                cap = info.get("capacity") or 0
                densities[z] = info["count"] / cap if cap > 0 else 0.0
            trend.add_density(densities)
            growth = trend.growth_rate()

            # risk
            assessed = engine.assess(counts, capacities, growth)

            # persist and alert
            for zone, data in assessed.items():
                db.insert_metric(
                    zone,
                    data["count"],
                    data["density"],
                    data["risk_level"],
                )
            _ = alerts.check({z: {"risk_level": d["risk_level"]} for z, d in assessed.items()})

            # simple console log
            print(assessed)
            time.sleep(FRAME_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("Stopping detection loop")
    finally:
        sampler.close()


if __name__ == "__main__":
    main()
