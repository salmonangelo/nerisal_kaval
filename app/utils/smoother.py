from collections import defaultdict, deque
from typing import Dict, Optional

class RollingAverage:
    def __init__(self, window: int = 5):
        self.window = window
        self.history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window))

    def update(self, key: str, value: float) -> float:
        """Add new value for key and return smoothed value."""
        self.history[key].append(value)
        return sum(self.history[key]) / len(self.history[key])
