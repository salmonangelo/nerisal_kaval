import cv2
import numpy as np

class ZoneOverlay:
    """Visualization for zone polygons and risk status."""

    def __init__(self):
        # Risk colors in BGR
        self.colors = {
            "Green": (0, 255, 0),
            "Amber": (0, 165, 255),
            "Red": (0, 0, 255)
        }

    def draw(self, frame: np.ndarray, zone_polygons: dict, assessed: dict) -> np.ndarray:
        """Draw zone polygons, names, counts, and density labels based on risk status.
        
        Args:
            frame: Input BGR frame.
            zone_polygons: Dict mapping zone names to lists of (x, y) coordinates.
            assessed: Dict mapping zone names to assessment metrics (risk_level, count, density_class).
            
        Returns:
            Annotated frame copy.
        """
        annotated = frame.copy()
        
        for name, points in zone_polygons.items():
            data = assessed.get(name, {})
            risk = data.get("risk_level", "Green")
            count = data.get("count", 0)
            d_class = data.get("density_class", "Empty")
            
            color = self.colors.get(risk, (0, 255, 0))
            
            # 1. Draw zone polygon
            pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated, [pts], isClosed=True, color=color, thickness=3)
            
            # 2. Add text status near the top-left of the polygon
            if len(points) > 0:
                # Find the 'label position' (upper boundary)
                label_y = min([p[1] for p in points])
                label_x = min([p[0] for p in points if p[1] == label_y])

                
                # Offset slightly inside the frame
                origin = (max(label_x, 20), max(label_y - 10, 30))
                
                text = f"{name} | {count} ppl | {d_class}"
                cv2.putText(annotated, text, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
        return annotated
