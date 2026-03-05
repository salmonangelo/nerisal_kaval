from typing import Dict, Optional
from ..config import RISK_THRESHOLDS, RISK_WEIGHTS


class RiskEngine:
    """Compute density and risk levels for zones."""

    def assess(
        self,
        counts: Dict[str, int],
        capacities: Dict[str, Optional[int]],
        growth_rates: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Return per-zone metrics.

        Output dict structure:
            { zone: {"count": int,
                     "capacity": float or None,
                     "density": float,
                     "growth": float,
                     "risk_score": float,
                     "risk_level": str } }
        """
        result: Dict[str, Dict[str, float]] = {}
        for zone, count in counts.items():
            cap = capacities.get(zone)
            density = count / cap if cap and cap > 0 else 0.0
            growth = 0.0
            if growth_rates and zone in growth_rates:
                growth = growth_rates[zone]
            # combine using weights
            score = (
                density * RISK_WEIGHTS.get("density", 0.5)
                + growth * RISK_WEIGHTS.get("growth", 0.5)
            )
            # determine level by thresholds
            if score >= RISK_THRESHOLDS["amber"]:
                level = "Red"
            elif score >= RISK_THRESHOLDS["green"]:
                level = "Amber"
            else:
                level = "Green"
            result[zone] = {
                "count": count,
                "capacity": cap,
                "density": density,
                "growth": growth,
                "risk_score": score,
                "risk_level": level,
            }
        return result
