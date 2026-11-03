"""AI RFQ Intake & Historical Routing Similarity Engine.

Extracts structured fields with document provenance & confidence scores,
and recommends manufacturing routings from the 1,400-row historical quote DB.
"""

from typing import Dict, List
from backend.costing_engine import AIExtractedField


MATERIAL_ALIASES = {
    "EN-8": "EN8",
    "EN-8D": "EN8",
    "080M40": "EN8",
    "EN8": "EN8",
    "40CR4": "40Cr4 forging",
    "40CR4 FORGING": "40Cr4 forging",
    "20MNCR5": "20MnCr5",
    "16MNCR5": "20MnCr5",
    "SAE8620": "SAE8620",
}


def normalize_material_grade(raw_grade: str) -> str:
    cleaned = (raw_grade or "").strip().upper()
    return MATERIAL_ALIASES.get(cleaned, raw_grade.strip())


def detect_document_conflicts(excel_row: Dict[str, str], drawing_ocr: Dict[str, str]) -> List[AIExtractedField]:
    """Compares Excel part list row against CAD Drawing Title Block OCR and flags discrepancies."""
    fields: List[AIExtractedField] = []

    excel_mat = normalize_material_grade(excel_row.get("material", ""))
    drw_mat = normalize_material_grade(drawing_ocr.get("material", ""))

    if excel_mat == drw_mat:
        fields.append(
            AIExtractedField(
                key="material_grade",
                value=excel_mat,
                source_document="Excel Col D + Drawing Title Block (Matched)",
                confidence_pct=98,
                accepted_by_estimator=False,
            )
        )
    else:
        fields.append(
            AIExtractedField(
                key="material_grade",
                value=excel_mat,
                source_document=f"CONFLICT: Excel='{excel_mat}' vs Drawing='{drw_mat}'",
                confidence_pct=52,
                accepted_by_estimator=False,
            )
        )

    fields.append(
        AIExtractedField(
            key="gross_wt_kg",
            value=str(excel_row.get("gross_wt_kg", "0.0")),
            source_document="Excel Part List Col E",
            confidence_pct=96 if "blur" not in drawing_ocr.get("notes", "").lower() else 62,
            accepted_by_estimator=False,
        )
    )
    return fields


def suggest_routing_from_history(
    material_grade: str,
    gross_wt_kg: float,
    historical_quotes: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    """Finds top matching historical parts by material grade and gross weight proximity."""
    candidates = []
    for row in historical_quotes:
        mat_match = 1.0 if row["material"] == material_grade else 0.4
        wt_diff = abs(float(row["gross_wt_kg"]) - gross_wt_kg) / max(0.1, gross_wt_kg)
        wt_score = max(0.0, 1.0 - wt_diff)
        similarity = round((0.65 * mat_match + 0.35 * wt_score) * 100, 1)
        candidates.append({**row, "similarity_pct": similarity})

    candidates.sort(key=lambda x: x["similarity_pct"], reverse=True)
    return candidates[:3]
