import math
from typing import List, Dict, Union, Tuple

class SimpleTracker:
    def __init__(self, max_distance: float = 100.0):
        self.max_distance = max_distance
        self.next_id = 1
        # store dict of id: (cx, cy)
        self.objects = {}

    def update(self, boxes: List[Union[List, Tuple]]) -> List[Dict]:
        """Update tracker with new bounding boxes.

        Args:
            boxes: List of [x1, y1, x2, y2]
        
        Returns:
            List of dicts: [{"id": int, "bbox": [x1, y1, x2, y2]}, ...]
        """
        if not boxes:
            self.objects.clear()
            return []

        # If no previous objects, register all
        if not self.objects:
            tracked = []
            for box in boxes:
                cx = (box[0] + box[2]) / 2.0
                cy = (box[1] + box[3]) / 2.0
                self.objects[self.next_id] = (cx, cy)
                tracked.append({"id": self.next_id, "bbox": box})
                self.next_id += 1
            return tracked

        # Match new boxes to existing objects based on centroid distance
        new_objects = {}
        tracked = []
        
        used_boxes = set()
        used_ids = set()

        # O(N^2) greedy matching is fine for low density. 
        # For high density, performance could degrade. CPU constrained per requirements, 
        # relying on small frame sizes or low count counts.
        for obj_id, (cx, cy) in self.objects.items():
            best_dist = float('inf')
            best_box_idx = -1
            best_box = None
            best_box_cents = None

            for i, box in enumerate(boxes):
                if i in used_boxes:
                    continue
                ncx = (box[0] + box[2]) / 2.0
                ncy = (box[1] + box[3]) / 2.0
                dist = math.hypot(cx - ncx, cy - ncy)

                if dist < self.max_distance and dist < best_dist:
                    best_dist = dist
                    best_box_idx = i
                    best_box = box
                    best_box_cents = (ncx, ncy)

            if best_box_idx != -1:
                used_boxes.add(best_box_idx)
                used_ids.add(obj_id)
                new_objects[obj_id] = best_box_cents
                tracked.append({"id": obj_id, "bbox": best_box})

        # Register new objects
        for i, box in enumerate(boxes):
            if i not in used_boxes:
                ncx = (box[0] + box[2]) / 2.0
                ncy = (box[1] + box[3]) / 2.0
                new_objects[self.next_id] = (ncx, ncy)
                tracked.append({"id": self.next_id, "bbox": box})
                self.next_id += 1

        self.objects = new_objects
        return tracked
