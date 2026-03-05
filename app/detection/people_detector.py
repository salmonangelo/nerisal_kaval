from ultralytics import YOLO
import numpy as np
from ..config import YOLO_MODEL_NAME


class PeopleDetector:
    def __init__(self, model_path: str = None):
        path = model_path or YOLO_MODEL_NAME
        self.model = YOLO(path)

    def detect(self, frame: np.ndarray) -> dict:
        """Run the model on a frame and return person count and boxes.

        Args:
            frame: numpy array (BGR or RGB) image

        Returns:
            dict with keys:
              - "count": int number of people detected
              - "boxes": list of [x1, y1, x2, y2] coordinates
        """
        results = self.model(frame)
        boxes = []
        for r in results:
            for box in r.boxes:
                if int(box.cls) == 0:  # person class
                    # box.xyxy may be a nested list (shape 1x4); flatten it
                    coords = box.xyxy.tolist()
                    if isinstance(coords, list) and len(coords) == 1 and isinstance(coords[0], (list, tuple)):
                        coords = coords[0]
                    boxes.append(coords)
        return {"count": len(boxes), "boxes": boxes}
