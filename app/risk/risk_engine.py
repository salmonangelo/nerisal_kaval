from typing import Dict, Optional, Any
from ..config import RISK_THRESHOLDS, RISK_WEIGHTS
from ..detection.density_classifier import DensityClassifier


class RiskEngine:
    """Compute density and risk levels for zones."""

    def __init__(self):
        self.classifier = DensityClassifier()
        self._levels = {"Red": 3, "Amber": 2, "Green": 1}

    def _worst(self, l1: str, l2: str) -> str:
        return l1 if self._levels.get(l1, 0) >= self._levels.get(l2, 0) else l2

    def assess(
        self,
        densities: Dict[str, float],
        local_densities: Dict[str, float],
        counts: Dict[str, int],
        capacities: Dict[str, Optional[int]],
        growth_rates: Optional[Dict[str, float]] = None,
        cluster_results: Optional[Dict[str, tuple]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Return per-zone metrics.

        Output dict structure:
            { zone: {"count": int,
                     "capacity": float or None,
                     "density": float,
                     "local_density": float,
                     "growth": float,
                     "risk_score": float,
                     "risk_level": str } }
        """
        result: Dict[str, Dict[str, float]] = {}
        for zone, density in densities.items():
            count = counts.get(zone, 0)
            cap = capacities.get(zone)
            local_density = local_densities.get(zone, 0.0)
            
            growth = 0.0
            if growth_rates and zone in growth_rates:
                growth = growth_rates[zone]
                
            # combine using weights (0.5 * density + 0.3 * local_density + 0.2 * growth)
            score = (
                density * 0.5
                + local_density * 0.3
                + growth * 0.2
            )
            
            # 1. Density Risk
            dens_label, dens_risk = self.classifier.classify(density)
            
            # 2. Growth Risk
            grow_risk = "Green"
            if growth > 0.5:
                grow_risk = "Red"
            elif growth > 0.3:
                grow_risk = "Amber"
                
            # 3. Cluster Risk
            c_res = cluster_results.get(zone, (False, 0.0, (0, 0), "Green")) if cluster_results else (False, 0.0, (0, 0), "Green")
            c_detected, c_ratio, c_center, c_risk = c_res

            # 4. Final Risk Determination (Simplified Logic)
            if density >= 0.9 or score >= 0.7:
                level = "Red"
            elif density < 0.3 and score < 0.3:
                level = "Green"
            else:
                level = "Amber"

            result[zone] = {
                "count": count,
                "capacity": cap,
                "density": density,
                "local_density": local_density,
                "growth": growth,
                "risk_score": score,
                "risk_level": level,
                "density_class": dens_label,
                "cluster_detected": 1 if c_detected else 0,
                "cluster_risk": c_risk,
                "cluster_ratio": c_ratio,
                "hotspot_center": c_center
            }
        return result
