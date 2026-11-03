"""Deterministic Multi-Volume Part Costing & Rate Master Versioning Engine.

Company A (Chakan, Pune) — Auto-Component RFQ-to-Quote System.
All cost math uses fixed deterministic formulas (never AI).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class MaterialRate:
    grade: str
    spec: str
    base_rate_inr_per_kg: float
    scrap_rate_inr_per_kg: float


@dataclass(frozen=True)
class MachineRate:
    code: str
    name: str
    rate_inr_per_hr: float


@dataclass(frozen=True)
class RateMasterSnapshot:
    snapshot_id: str
    effective_from: str
    effective_to: Optional[str]
    status: str  # "Active" | "Superseded"
    materials: Dict[str, MaterialRate]
    machines: Dict[str, MachineRate]


@dataclass
class RoutingOperation:
    op_no: int
    name: str
    cycle_time_min: float
    hour_rate_inr: float
    setup_time_min: float = 60.0


@dataclass
class AIExtractedField:
    key: str
    value: str
    source_document: str
    confidence_pct: int
    accepted_by_estimator: bool = False
    overridden_by: Optional[str] = None


@dataclass
class PartRFQ:
    rfq_no: str
    customer: str
    part_name: str
    material_grade: str
    gross_wt_kg: float
    net_wt_kg: float
    annual_volume: int
    rate_snapshot_id: str
    operations: List[RoutingOperation]
    rejection_pct: float = 1.5
    overhead_pct: float = 14.0
    packing_per_pc_inr: float = 1.40
    freight_per_pc_inr: float = 1.10
    margin_pct: float = 12.0
    batches_per_year: int = 12
    status: str = "Estimating"
    status_reason: str = ""
    owner: str = "Rajesh Kulkarni"
    routing_verified_by: Optional[str] = None
    approved_by_sales_head: Optional[str] = None
    ai_fields: List[AIExtractedField] = field(default_factory=list)


SALES_HEAD_APPROVAL_THRESHOLD_INR = 2_500_000.0  # ₹25.00 Lakh annual value
GST_RATE_PCT = 18.0
SWARF_RECOVERY_FACTOR = 0.90


def get_seeded_rate_masters() -> Dict[str, RateMasterSnapshot]:
    return {
        "RM-2026-Q4": RateMasterSnapshot(
            snapshot_id="RM-2026-Q4",
            effective_from="2026-10-01",
            effective_to=None,
            status="Active",
            materials={
                "EN8": MaterialRate("EN8", "BS 970 080M40 Bright Bar", 78.00, 32.00),
                "40Cr4 forging": MaterialRate("40Cr4 forging", "IS 40Cr4 Closed-Die Forging", 104.00, 36.00),
                "20MnCr5": MaterialRate("20MnCr5", "DIN 17210 Case Hardening Steel", 92.00, 34.00),
                "SAE8620": MaterialRate("SAE8620", "ASTM A29 Alloy Gear Steel", 96.00, 35.00),
            },
            machines={
                "CNC-TURN-CELL": MachineRate("CNC-TURN-CELL", "CNC Turning + Centerless Grinding", 850.0),
                "FORGE-VMC-HEAVY": MachineRate("FORGE-VMC-HEAVY", "1600T Forging Press + 4-Axis VMC", 1450.0),
                "GEAR-TURN-HOB": MachineRate("GEAR-TURN-HOB", "CNC Turn-Mill + Gear Blank Cell", 950.0),
            },
        ),
        "RM-2026-Q3": RateMasterSnapshot(
            snapshot_id="RM-2026-Q3",
            effective_from="2026-07-01",
            effective_to="2026-09-30",
            status="Superseded",
            materials={
                "EN8": MaterialRate("EN8", "BS 970 080M40 Bright Bar", 74.50, 30.00),
                "40Cr4 forging": MaterialRate("40Cr4 forging", "IS 40Cr4 Closed-Die Forging", 98.00, 34.00),
                "20MnCr5": MaterialRate("20MnCr5", "DIN 17210 Case Hardening Steel", 88.00, 32.00),
                "SAE8620": MaterialRate("SAE8620", "ASTM A29 Alloy Gear Steel", 91.50, 33.00),
            },
            machines={
                "CNC-TURN-CELL": MachineRate("CNC-TURN-CELL", "CNC Turning + Centerless Grinding", 820.0),
                "FORGE-VMC-HEAVY": MachineRate("FORGE-VMC-HEAVY", "1600T Forging Press + 4-Axis VMC", 1390.0),
                "GEAR-TURN-HOB": MachineRate("GEAR-TURN-HOB", "CNC Turn-Mill + Gear Blank Cell", 910.0),
            },
        ),
    }


def compute_cost_at_volume(
    rfq: PartRFQ,
    rate_masters: Dict[str, RateMasterSnapshot],
    volume: int,
) -> Dict[str, float]:
    """Computes deterministic piece cost breakdown at a target annual volume."""
    if volume <= 0:
        raise ValueError("Annual volume must be positive")
    if rfq.gross_wt_kg <= 0 or rfq.net_wt_kg <= 0:
        raise ValueError("Part weights must be positive")
    if rfq.net_wt_kg > rfq.gross_wt_kg:
        raise ValueError("Net weight cannot exceed gross weight")

    if rfq.rate_snapshot_id not in rate_masters:
        raise KeyError(f"Unknown Rate Master Snapshot: {rfq.rate_snapshot_id}")

    snapshot = rate_masters[rfq.rate_snapshot_id]
    if rfq.material_grade not in snapshot.materials:
        raise KeyError(f"Material {rfq.material_grade} not found in snapshot {rfq.rate_snapshot_id}")

    mat = snapshot.materials[rfq.material_grade]

    # 1. Material & Scrap Credit
    gross_mat_cost = round(rfq.gross_wt_kg * mat.base_rate_inr_per_kg, 4)
    scrap_wt = max(0.0, rfq.gross_wt_kg - rfq.net_wt_kg)
    scrap_credit = round(scrap_wt * SWARF_RECOVERY_FACTOR * mat.scrap_rate_inr_per_kg, 4)
    net_mat_cost = round(gross_mat_cost - scrap_credit, 4)

    # 2. Routing Conversion & Batch Setup Amortization
    total_cycle_min = sum(op.cycle_time_min for op in rfq.operations)
    total_run_cost = sum((op.cycle_time_min / 60.0) * op.hour_rate_inr for op in rfq.operations)
    total_setup_cost_per_batch = sum((op.setup_time_min / 60.0) * op.hour_rate_inr for op in rfq.operations)

    batch_size = max(1.0, volume / max(1, rfq.batches_per_year))
    setup_cost_per_pc = total_setup_cost_per_batch / batch_size
    total_conversion_cost = round(total_run_cost + setup_cost_per_pc, 4)

    # 3. Prime Cost, Process Rejection & Overhead Absorption
    prime_cost = net_mat_cost + total_conversion_cost
    rejection_cost = prime_cost * (rfq.rejection_pct / 100.0)

    vol_ratio = volume / max(1, rfq.annual_volume)
    oh_multiplier = 1.06 if vol_ratio < 0.8 else (0.96 if vol_ratio > 1.2 else 1.0)
    overhead_cost = total_conversion_cost * (rfq.overhead_pct / 100.0) * oh_multiplier

    # 4. Packing, Freight, Total Manufacturing Cost & Margin
    total_mfg_cost = prime_cost + rejection_cost + overhead_cost + rfq.packing_per_pc_inr + rfq.freight_per_pc_inr
    margin_inr = total_mfg_cost * (rfq.margin_pct / 100.0)
    unit_price_ex_gst = round(total_mfg_cost + margin_inr, 2)
    gst_inr = round(unit_price_ex_gst * (GST_RATE_PCT / 100.0), 2)
    unit_price_incl_gst = round(unit_price_ex_gst + gst_inr, 2)
    annual_value_ex_gst = round(unit_price_ex_gst * volume, 2)

    return {
        "volume": volume,
        "batch_size": round(batch_size),
        "rate_snapshot_id": rfq.rate_snapshot_id,
        "gross_material_cost": round(gross_mat_cost, 2),
        "scrap_credit": round(scrap_credit, 2),
        "net_material_cost": round(net_mat_cost, 2),
        "total_cycle_min": round(total_cycle_min, 2),
        "run_cost_per_pc": round(total_run_cost, 2),
        "setup_cost_per_pc": round(setup_cost_per_pc, 2),
        "total_conversion_cost": round(total_conversion_cost, 2),
        "rejection_cost": round(rejection_cost, 2),
        "overhead_cost": round(overhead_cost, 2),
        "packing_and_freight": round(rfq.packing_per_pc_inr + rfq.freight_per_pc_inr, 2),
        "total_manufacturing_cost": round(total_mfg_cost, 2),
        "margin_inr": round(margin_inr, 2),
        "unit_price_ex_gst": unit_price_ex_gst,
        "gst_18_pct": gst_inr,
        "unit_price_incl_gst": unit_price_incl_gst,
        "annual_value_ex_gst": annual_value_ex_gst,
        "requires_sales_head_approval": annual_value_ex_gst > SALES_HEAD_APPROVAL_THRESHOLD_INR,
    }


def validate_quote_release(rfq: PartRFQ, rate_masters: Dict[str, RateMasterSnapshot], actor_role: str) -> None:
    """Enforces AI acceptance and > ₹25L Sales Head approval rules."""
    unaccepted = [f.key for f in rfq.ai_fields if not f.accepted_by_estimator]
    if unaccepted:
        raise PermissionError(
            f"Quote release blocked: AI-extracted fields pending Estimator acceptance: {', '.join(unaccepted)}"
        )

    cost = compute_cost_at_volume(rfq, rate_masters, rfq.annual_volume)
    if cost["requires_sales_head_approval"] and not rfq.approved_by_sales_head:
        if actor_role not in ("sales_head", "md"):
            raise PermissionError(
                f"Quote annual value ₹{cost['annual_value_ex_gst']:,.2f} exceeds ₹25,00,000 threshold. "
                "Requires Sales Head approval."
            )
