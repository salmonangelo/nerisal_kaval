from typing import Dict, List, Tuple


class ZoneFlowTracker:
    """Track movement of people between zones across frames."""

    def __init__(self):
        """Initialize flow tracker.
        
        Attributes:
            last_zone: Dict mapping object_id → last known zone
            flow_counts: Dict mapping (from_zone, to_zone) → movement count
        """
        self.last_zone: Dict[int, str] = {}
        self.flow_counts: Dict[Tuple[str, str], int] = {}

    def update(
        self,
        tracked_objects: List[Dict],
        zone_assignments: Dict[int, str]
    ) -> None:
        """Update flow tracker with current tracked objects and zone assignments.

        Args:
            tracked_objects: List of tracked object dicts [{"id": int, "bbox": [...], "centroid": (x,y)}, ...]
            zone_assignments: Dict mapping object_id → zone_name (e.g., {1: "Zone_A", 2: "Zone_B"})
        
        Logic:
            1. For each tracked object with a current zone assignment
            2. Check if it has a previous zone in memory
            3. If zones differ, record flow movement
            4. Update memory with current zone
        """
        for obj in tracked_objects:
            obj_id = obj["id"]
            current_zone = zone_assignments.get(obj_id)

            # Check if this object has moved between zones
            if obj_id in self.last_zone:
                prev_zone = self.last_zone[obj_id]

                # Movement detected: zone changed and current zone is not None
                if prev_zone != current_zone and current_zone is not None:
                    key = (prev_zone, current_zone)
                    self.flow_counts[key] = self.flow_counts.get(key, 0) + 1

            # Update memory with current zone (if assigned)
            if current_zone is not None:
                self.last_zone[obj_id] = current_zone

    def get_flows(self) -> Dict[Tuple[str, str], int]:
        """Return current flow counts.

        Returns:
            Dict mapping (from_zone, to_zone) → count
            Example: {("Zone_A", "Zone_B"): 3, ("Zone_B", "Zone_A"): 1}
        """
        return self.flow_counts

    def get_flows_formatted(self) -> List[Dict]:
        """Return flows in formatted list for API.

        Returns:
            List of dicts with 'from', 'to', 'count' keys
            Example: [{"from": "Zone_A", "to": "Zone_B", "count": 3}, ...]
        """
        result = []
        for (from_zone, to_zone), count in self.flow_counts.items():
            result.append({
                "from": from_zone,
                "to": to_zone,
                "count": count
            })
        return result

    def reset_flows(self) -> None:
        """Reset flow counts (call this at end of iteration if needed for fresh counts each period)."""
        self.flow_counts.clear()

    def prune_stale_objects(self, active_object_ids: List[int]) -> None:
        """Remove tracking for objects that are no longer detected.

        Args:
            active_object_ids: List of currently tracked object IDs
        """
        stale_ids = [oid for oid in self.last_zone.keys() if oid not in active_object_ids]
        for oid in stale_ids:
            del self.last_zone[oid]
