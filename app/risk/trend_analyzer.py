from typing import List, Dict


class TrendAnalyzer:
    def __init__(self):
        # maintain up to three recent density snapshots per zone
        self.history: List[Dict[str, float]] = []
        self.window_size = 3

    def add_density(self, densities: Dict[str, float]):
        """Add latest density readings (zone -> value).

        Keeps only the most recent `window_size` entries.
        """
        self.history.append(densities.copy())
        if len(self.history) > self.window_size:
            self.history.pop(0)

    def rolling_average(self) -> Dict[str, float]:
        """Compute rolling average density for each zone."""
        if not self.history:
            return {}
        totals: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        for entry in self.history:
            for zone, val in entry.items():
                totals[zone] = totals.get(zone, 0.0) + val
                counts[zone] = counts.get(zone, 0) + 1
        return {zone: totals[zone] / counts[zone] for zone in totals}

    def growth_rate(self) -> Dict[str, float]:
        """Compute growth rate based on the oldest and newest values.

        (latest - oldest) / oldest if oldest > 0, else 0.
        """
        if len(self.history) < 2:
            return {}
        first = self.history[0]
        last = self.history[-1]
        rates: Dict[str, float] = {}
        for zone, new_val in last.items():
            old_val = first.get(zone, 0.0)
            if old_val > 0:
                rates[zone] = (new_val - old_val) / old_val
            else:
                rates[zone] = 0.0
        return rates
