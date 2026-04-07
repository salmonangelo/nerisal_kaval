from dataclasses import dataclass
from typing import List, Tuple, Optional, Union


@dataclass
class RectZone:
    name: str
    x1: int
    y1: int
    x2: int
    y2: int
    capacity: Optional[int] = None
    source: Optional[Union[int, str]] = None
    triggers_alert_for: Optional[str] = None  # name of another zone to alert if this one is critical

    @property
    def points(self) -> List[Tuple[int, int]]:
        return [
            (self.x1, self.y1),
            (self.x2, self.y1),
            (self.x2, self.y2),
            (self.x1, self.y2),
        ]


@dataclass
class ZoneConfig:
    zones: List[RectZone]
