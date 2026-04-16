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

    def map_boxes(self, boxes: List[Tuple[float, float, float, float]], frame_shape: Tuple[int, int] = (1080, 1920), grid_size: Tuple[int, int] = (5, 5)) -> Dict[str, Dict[str, ...]]:
        """Given a list of bounding boxes, count how many fall in each zone and compute local grid density.
        
        Uses bottom-center point.
        """
        if boxes is None:
            boxes = []
        if isinstance(boxes, (list, tuple)) and len(boxes) == 4 and not hasattr(boxes[0], '__iter__'):
            boxes = [boxes]
            
        points_in_zone: Dict[str, List[Tuple[float, float]]] = {name: [] for name in self.polygons}
        
        boxes_in_zone: Dict[str, List] = {name: [] for name in self.polygons}

        for item in boxes:
            try:
                x1, y1, x2, y2 = item
            except Exception:
                print(f"Skipping invalid box entry: {item}")
                continue
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0  # true centroid for consistency with heatmap
            zone = self.map_point(cx, cy)
            if zone:
                points_in_zone[zone].append((cx, cy))
                boxes_in_zone[zone].append(item)
                
        result = {}
        height, width = frame_shape[:2]
        rows, cols = grid_size
        
        for name, points in points_in_zone.items():
            count = len(points)
            cap = self.capacities.get(name)

            # compute dynamic local density (max grid cell count within this zone)
            cell_counts = {}
            for px, py in points:
                c = min(cols - 1, max(0, int((px / width) * cols)))
                r = min(rows - 1, max(0, int((py / height) * rows)))
                cell_counts[(r, c)] = cell_counts.get((r, c), 0) + 1
                
            local_density = max(cell_counts.values()) if cell_counts else 0
            
            result[name] = {
                "count": count, 
                "capacity": cap,
                "local_density": local_density,
                "detections": boxes_in_zone[name]
            }
        return result
