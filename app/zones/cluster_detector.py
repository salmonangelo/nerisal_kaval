import numpy as np
import cv2

class ClusterDetector:
    """Detects localized hotspots ('clusters') within zones on a heatmap."""

    def __init__(self, hotspot_threshold: float = 0.75):
        self.hotspot_threshold = hotspot_threshold

    def detect_clusters(self, heatmap: np.ndarray, polygon: list, capacity: int) -> tuple:
        """Mask heatmap, find hotspots above threshold, and calculate cluster ratio.
        
        Args:
            heatmap: Normalized float32 heatmap (0 to 1).
            polygon: List of points [(x1, y1), (x2, y2), ...].
            capacity: Threshold for population check (used as context).
            
        Returns:
            (cluster_detected: bool,
             cluster_ratio: float,
             hotspot_center: tuple,
             cluster_risk: str)
        """
        h, w = heatmap.shape[:2]
        
        # 1. Create zone mask
        mask = np.zeros((h, w), dtype=np.uint8)
        pts = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [pts], 1)
        
        # Total area of the zone (in pixels)
        zone_area = np.sum(mask)
        if zone_area == 0:
            return False, 0.0, (0, 0), "Green"
            
        # 2. Mask the heatmap and find hotspot pixels
        masked_h = heatmap * mask
        hotspots = masked_h > self.hotspot_threshold
        hotspot_area = np.sum(hotspots)
        
        # 3. Calculate spatial density ratio (proportion of zone that is a hotspot)
        cluster_ratio = hotspot_area / zone_area
        
        # 4. Find center of hotspot mass
        hotspot_coords = np.where(hotspots)
        if len(hotspot_coords[0]) > 0:
            cy, cx = int(np.mean(hotspot_coords[0])), int(np.mean(hotspot_coords[1]))
            hotspot_center = (cx, cy)
        else:
            hotspot_center = (0, 0)
            
        # 5. Determine cluster-specific risk thresholds
        if cluster_ratio > 0.3:
            cluster_risk = "Red"
        elif cluster_ratio > 0.15:
            cluster_risk = "Amber"
        else:
            cluster_risk = "Green"
            
        cluster_detected = hotspot_area > 0
        
        return cluster_detected, cluster_ratio, hotspot_center, cluster_risk
