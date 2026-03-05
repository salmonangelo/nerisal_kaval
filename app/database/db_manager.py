import sqlite3
from typing import Dict, List, Any


class DBManager:
    def __init__(self, db_url: str):
        self.conn = sqlite3.connect(db_url, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                zone TEXT,
                count INTEGER,
                density_ratio REAL,
                risk_level TEXT
            )
            """
        )
        self.conn.commit()

    def insert_metric(
        self,
        zone: str,
        count: int,
        density_ratio: float,
        risk_level: str,
    ) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO metrics (zone, count, density_ratio, risk_level)
            VALUES (?, ?, ?, ?)
            """,
            (zone, count, density_ratio, risk_level),
        )
        self.conn.commit()

    def get_latest_status(self) -> List[Dict[str, Any]]:
        """Return the most recent entry for each zone."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT m1.* FROM metrics m1
            INNER JOIN (
                SELECT zone, MAX(timestamp) as ts FROM metrics GROUP BY zone
            ) m2 ON m1.zone = m2.zone AND m1.timestamp = m2.ts
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_zone_history(self, zone: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM metrics WHERE zone = ? ORDER BY timestamp", (zone,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
