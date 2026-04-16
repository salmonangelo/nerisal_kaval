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
        """Draw zone polygons with filled transparent overlay, labels, and counts.
        
        Args:
            frame: Input BGR frame.
            zone_polygons: Dict mapping zone names to lists of (x, y) coordinates.
            assessed: Dict mapping zone names to assessment metrics (risk_level, count, density_class).
            
        Returns:
            Annotated frame copy.
        """
        annotated = frame.copy()
        
        # Helper function to draw a filled transparent rectangle
        def draw_filled_zone(img, x1, y1, x2, y2, color, alpha=0.15):
            overlay = img.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        for name, points in zone_polygons.items():
            data = assessed.get(name, {})
            risk = data.get("risk_level", "Green")
            count = data.get("count", 0)
            d_class = data.get("density_class", "Empty")
            
            color = self.colors.get(risk, (0, 255, 0))
            
            # 1. Draw filled transparent zone background
            if len(points) >= 2:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                annotated = draw_filled_zone(annotated, x_min, y_min, x_max, y_max, color, alpha=0.12)
                
                # 2. Draw zone border (solid line)
                pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated, [pts], isClosed=True, color=color, thickness=3)
            
            # 3. Add structured text label with background box
            if len(points) > 0:
                # Position label at top-left of zone
                label_x = min([p[0] for p in points]) + 10
                label_y = min([p[1] for p in points]) + 30
                
                # Multi-line label
                lines = [
                    f"{name}",
                    f"{count} people",
                    f"Density: {d_class}"
                ]
                
                # Draw background box for text
                max_text_width = max([len(line) for line in lines]) * 8
                text_height = len(lines) * 22 + 8
                bg_x1 = max(label_x - 5, 2)
                bg_y1 = max(label_y - 20, 2)
                bg_x2 = min(bg_x1 + max_text_width, annotated.shape[1] - 2)
                bg_y2 = min(bg_y1 + text_height, annotated.shape[0] - 2)
                
                cv2.rectangle(annotated, (bg_x1, bg_y1), (bg_x2, bg_y2), color, -1)
                
                # Draw text lines
                for i, line in enumerate(lines):
                    y_offset = label_y + (i * 18)
                    cv2.putText(annotated, line, (label_x, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
        return annotated
