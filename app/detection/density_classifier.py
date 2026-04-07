from typing import Tuple

class DensityClassifier:
    """Classifies crowd density and maps to risk levels."""

    def classify(self, density_ratio: float) -> Tuple[str, str]:
        """Classify based on predefined thresholds.
        
        Returns:
            (label, risk_level)
        """
        if density_ratio >= 0.85:
            return "Dense", "Red"
        elif density_ratio >= 0.55:
            return "Medium", "Amber"
        elif density_ratio >= 0.20:
            return "Sparse", "Green"
        else:
            return "Empty", "Green"


# Support for legacy function for backwards compatibility
def get_density_label(density: float) -> str:
    """Legacy helper for get_density_label."""
    label, _ = DensityClassifier().classify(density)
    return label
