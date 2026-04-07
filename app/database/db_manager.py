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
        
        # Safely upgrade schema
        try:
            cursor.execute("ALTER TABLE metrics ADD COLUMN local_density REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # column already exists
            
        try:
            cursor.execute("ALTER TABLE metrics ADD COLUMN density_class TEXT DEFAULT 'Empty'")
        except sqlite3.OperationalError:
            pass  # column already exists

        # Clustering upgrades
        try:
            cursor.execute("ALTER TABLE metrics ADD COLUMN cluster_detected INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE metrics ADD COLUMN cluster_risk TEXT DEFAULT 'Green'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE metrics ADD COLUMN hotspot_x INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE metrics ADD COLUMN hotspot_y INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE metrics ADD COLUMN cluster_ratio REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass

        self.conn.commit()

    def insert_metric(
        self,
        zone: str,
        count: int,
        density_ratio: float,
        risk_level: str,
        local_density: float = 0.0,
        density_class: str = "Empty",
        cluster_detected: int = 0,
        cluster_risk: str = "Green",
        hotspot_x: int = 0,
        hotspot_y: int = 0,
        cluster_ratio: float = 0.0,
    ) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO metrics (
                zone, count, density_ratio, risk_level, local_density, density_class,
                cluster_detected, cluster_risk, hotspot_x, hotspot_y, cluster_ratio
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (zone, count, density_ratio, risk_level, local_density, density_class,
             cluster_detected, cluster_risk, hotspot_x, hotspot_y, cluster_ratio),
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
