import cv2
import numpy as np

class TrackingView:
    """Visualization for tracked objects and their centroids."""

    def draw(self, frame: np.ndarray, boxes: list) -> np.ndarray:
        """Draw green bounding boxes and centroid dots on the frame.
        
        Args:
            frame: Input BGR frame.
            boxes: List of bounding boxes [x1, y1, x2, y2].
            
        Returns:
            Annotated frame copy.
        """
        annotated = frame.copy()
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            
            # 1. Draw green bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 2. Draw centroid dot
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            cv2.circle(annotated, (cx, cy), 4, (0, 255, 0), -1)
            
        return annotated
