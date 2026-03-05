from shapely.geometry import Point, Polygon
from .zone_config import ZoneConfig
from typing import List, Tuple, Dict, Optional


class ZoneMapper:
    def __init__(self, config: ZoneConfig):
        # build polygon and capacity lookup
        self.polygons: Dict[str, Polygon] = {}
        self.capacities: Dict[str, Optional[int]] = {}
        for z in config.zones:
            self.polygons[z.name] = Polygon(z.points)
            self.capacities[z.name] = getattr(z, "capacity", None)

    def map_point(self, x: float, y: float) -> Optional[str]:
        """Return name of zone containing point or None."""
        pt = Point(x, y)
        for name, poly in self.polygons.items():
            if poly.contains(pt):
                return name
        return None

    def map_boxes(self, boxes: List[Tuple[float, float, float, float]]) -> Dict[str, Dict[str, Optional[int]]]:
        """Given a list of bounding boxes, count how many fall in each zone.

        Boxes are tuples (x1,y1,x2,y2). The zone is determined by the box center.
        Returns a dict keyed by zone name with 'count' and 'capacity'.
        """
        # normalize input: allow single flat box or numpy arrays
        if boxes is None:
            boxes = []
        # if the first element isn't iterable but there are 4 numbers, treat as one box
        if isinstance(boxes, (list, tuple)) and len(boxes) == 4 and not hasattr(boxes[0], '__iter__'):
            boxes = [boxes]
        counts: Dict[str, int] = {name: 0 for name in self.polygons}
        for item in boxes:
            try:
                x1, y1, x2, y2 = item
            except Exception:
                # fallback: print debug information then skip
                print(f"Skipping invalid box entry: {item}")
                continue
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            zone = self.map_point(cx, cy)
            if zone:
                counts[zone] += 1
        result: Dict[str, Dict[str, Optional[int]]] = {}
        for name, count in counts.items():
            result[name] = {"count": count, "capacity": self.capacities.get(name)}
        return result
