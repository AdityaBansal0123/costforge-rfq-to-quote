"""HTTP JSON API & SQLite Persistence Server for CostForge Chakan."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sqlite3
from backend.costing_engine import (
    PartRFQ,
    RoutingOperation,
    compute_cost_at_volume,
    get_seeded_rate_masters,
)

DB_PATH = os.environ.get("DATABASE_PATH", "chakan_costforge.db")


def init_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rfq_quotes (
            rfq_no TEXT PRIMARY KEY,
            customer TEXT NOT NULL,
            part_name TEXT NOT NULL,
            material_grade TEXT NOT NULL,
            gross_wt_kg REAL NOT NULL,
            net_wt_kg REAL NOT NULL,
            annual_volume INTEGER NOT NULL,
            cycle_time_min REAL NOT NULL,
            hour_rate_inr REAL NOT NULL,
            rate_snapshot_id TEXT NOT NULL,
            status TEXT NOT NULL,
            status_reason TEXT
        )
    """)
    # Seed users
    demo_users = [
        ("rajesh.kulkarni@companya-pune.in", "Rajesh Kulkarni", "estimator"),
        ("vikram.joshi@companya-pune.in", "Vikram Joshi", "sales_head"),
        ("anand.shinde@companya-pune.in", "Anand Shinde", "plant_head"),
    ]
    cur.executemany("INSERT OR IGNORE INTO users (email, name, role) VALUES (?, ?, ?)", demo_users)

    # Seed sample RFQs from prompt
    sample_rfqs = [
        ("RFQ-2611-014", "Company B (two-wheelers)", "Rear wheel spindle", "EN8", 0.61, 0.48, 180000, 3.2, 850.0, "RM-2026-Q4", "Pending Approval", "Awaiting Sales Head sign-off (> ₹25L)"),
        ("RFQ-2611-019", "Company C (tractors)", "Hydraulic lift arm", "40Cr4 forging", 4.60, 3.85, 24000, 11.5, 1450.0, "RM-2026-Q4", "Pending Approval", "Awaiting Sales Head sign-off (> ₹25L)"),
        ("RFQ-2611-023", "Company D (drivetrains)", "Gear blank", "20MnCr5", 1.48, 1.18, 60000, 4.8, 950.0, "RM-2026-Q4", "Estimating", "Costing in progress"),
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO rfq_quotes
        (rfq_no, customer, part_name, material_grade, gross_wt_kg, net_wt_kg, annual_volume, cycle_time_min, hour_rate_inr, rate_snapshot_id, status, status_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_rfqs)
    conn.commit()
    conn.close()


class CostForgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self._send_json(200, {"status": "ok", "plant": "Chakan MIDC Unit-II"})
            return
        if self.path == "/api/rfqs":
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute("SELECT * FROM rfq_quotes").fetchall()]
            conn.close()
            self._send_json(200, {"rfqs": rows})
            return
        # Serve Frontend UI
        ui_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if os.path.exists(ui_path):
            with open(ui_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
            return
        self._send_json(404, {"error": "Not found"})

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8000"))
    print(f"CostForge Chakan server listening on http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), CostForgeHandler).serve_forever()
