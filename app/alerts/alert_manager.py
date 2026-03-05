from typing import Dict, Any


class AlertManager:
    """Simple alert manager that triggers on 'Red' risk_level."""

    def check(self, statuses: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Inspect zone statuses and return alert payloads.

        Expected input format:
            { zone: {"risk_level": str, ...}, ... }
        """
        alerts: Dict[str, Dict[str, Any]] = {}
        for zone, info in statuses.items():
            level = info.get("risk_level")
            if level == "Red":
                msg = f"ALERT: {zone} has reached RED risk level!"
                print(msg)
                alerts[zone] = {"message": msg, **info}
        return alerts
