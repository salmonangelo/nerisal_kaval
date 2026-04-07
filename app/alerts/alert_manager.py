from typing import Dict, Any


class AlertManager:
    """Alert manager that triggers on 'Red' (critical) and 'Amber' (warning) levels."""

    def check(self, statuses: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Inspect zone statuses and return alert payloads."""
        alerts: Dict[str, Dict[str, Any]] = {}
        for zone, info in statuses.items():
            level = info.get("risk_level")
            cluster_status = " [CLUSTER DETECTED]" if info.get("cluster_detected") else ""
            if level == "Red":
                msg = f"CRITICAL: {zone} danger level reached!{cluster_status}"
                alerts[zone] = {"message": msg, "severity": "critical", **info}
            elif level == "Amber":
                msg = f"WARNING: {zone} showing elevated risk.{cluster_status}"
                alerts[zone] = {"message": msg, "severity": "warning", **info}
        return alerts

