"""Generates 1,400 realistic historical Chakan quote rows for Excel/CSV import testing."""

import csv
import os
import random

random.seed(42)

CUSTOMERS = [
    "Company B (two-wheelers)",
    "Company C (tractors)",
    "Company D (drivetrains)",
    "Company E (EV Transmissions)",
    "Bajaj Tier-1 Chakan Cluster",
    "Mahindra Farm Division Suppliers",
]

PARTS = [
    ("Rear wheel spindle", "EN8", 0.61, 0.48, 3.2, 850),
    ("Hydraulic lift arm", "40Cr4 forging", 4.60, 3.85, 11.5, 1450),
    ("Gear blank", "20MnCr5", 1.48, 1.18, 4.8, 950),
    ("Front fork lower bracket", "40Cr4 forging", 1.85, 1.52, 5.4, 1390),
    ("Countershaft 4th gear", "SAE8620", 1.38, 1.10, 4.5, 910),
    ("Swingarm pivot shaft", "EN8", 0.54, 0.43, 2.9, 820),
]

RATE_SNAPSHOTS = ["RM-2024-Q3", "RM-2025-Q1", "RM-2025-Q3", "RM-2026-Q1", "RM-2026-Q3"]


def generate_csv(out_path: str, count: int = 1400) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "quote_no", "quote_date", "customer", "part_name", "material_grade",
            "gross_wt_kg", "net_wt_kg", "annual_volume", "cycle_time_min",
            "hour_rate_inr", "rate_snapshot_id", "quoted_unit_price_inr", "outcome"
        ])
        for i in range(1, count + 1):
            base = PARTS[i % len(PARTS)]
            jitter = 1.0 + ((i % 9) - 4) * 0.015
            gross = round(base[2] * jitter, 2)
            net = round(base[3] * jitter, 2)
            cycle = round(base[4] * jitter, 2)
            vol = random.choice([12000, 24000, 48000, 60000, 120000, 180000])
            snap = RATE_SNAPSHOTS[i % len(RATE_SNAPSHOTS)]
            price = round((gross * 88.0) + (cycle / 60.0) * base[5] * 1.28, 2)
            outcome = "Won" if i % 5 != 0 else "Lost (Late Reply)"
            writer.writerow([
                f"QUOTE-{2400 + (i // 60):04d}-{i:04d}",
                f"2025-{(i % 12) + 1:02d}-{(i % 27) + 1:02d}",
                CUSTOMERS[i % len(CUSTOMERS)],
                f"{base[0]} Rev-{chr(65 + (i % 5))}",
                base[1],
                gross,
                net,
                vol,
                cycle,
                base[5],
                snap,
                price,
                outcome,
            ])


if __name__ == "__main__":
    out_csv = os.path.join(os.path.dirname(__file__), "..", "sample_data", "legacy_1400_past_quotes.csv")
    generate_csv(out_csv, 1400)
    print("Generated 1,400 historical quote rows at", out_csv)
