import cv2
import numpy as np

class TrackingView:
    """Visualization for tracked objects and their centroids."""

    def __init__(self):
        # Risk colors in BGR
        self.colors = {
            "Green": (0, 255, 0),
            "Amber": (0, 165, 255),
            "Red": (0, 0, 255)
        }

    def draw(self, frame: np.ndarray, boxes: list, risk_level: str = "Green") -> np.ndarray:
        """Draw bounding boxes with centroids, colored by risk level.
        
        Args:
            frame: Input BGR frame.
            boxes: List of bounding boxes as [x1, y1, x2, y2].
            risk_level: Risk level ("Green", "Amber", or "Red") for color coding.
            
        Returns:
            Annotated frame copy.
        """
        annotated = frame.copy()
        color = self.colors.get(risk_level, (0, 255, 0))
        
        for idx, box in enumerate(boxes):
            if len(box) >= 4:
                x1, y1, x2, y2 = map(int, box[:4])
                
                # 1. Draw bounding box with risk color
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
                # 2. Draw centroid
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                cv2.circle(annotated, (cx, cy), 5, color, -1)
                
                # 3. Optional: Draw index label
                label_text = f"{idx}"
                text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                label_y = max(y1 - 8, text_size[1] + 2)
                cv2.putText(annotated, label_text, (x1 + 2, label_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated
