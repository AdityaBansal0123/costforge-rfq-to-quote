# CostForge Chakan — Auto-Component RFQ-to-Quote Costing Workbench

**GitHub Repository**: [https://github.com/AdityaBansal0123/costforge-rfq-to-quote](https://github.com/AdityaBansal0123/costforge-rfq-to-quote)  

**Client Context**: Company A Precision Auto Components Pvt. Ltd. (MIDC Phase II, Chakan, Pune — 410501)

**Domain**: Precision Machined & Closed-Die Forged Components (Two-Wheeler, Tractor & Tier-1 Drivetrain OEMs)

**Target Outcome**: Cut RFQ-to-quote turnaround from **9 working days to ≤ 4 working days** and reduce estimator effort from **2.5 hours/part to ≤ 1.0 hour/part** with 100% rate traceability.

## Overview & Business Problem

Company A receives **60 RFQs per month** (\~720 RFQs/year) averaging **5 parts per RFQ** (3,600 parts/year). Under the legacy workflow—where estimators manually transcribe 2D CAD drawing title blocks, copy raw material and workcenter hour rates by hand from an old ERP into sprawling Excel sheets, and hunt through shared folders for historical quotes:

* **Direct Estimation Cost**: $720 \times 5 \times 2.5\text{ hrs} = 9,000\text{ estimator hours/year}$ at ₹450/hr = **₹40.50 Lakh/year**.

* **Lost Contribution from Late Replies**: 9-working-day turnaround against the 4-day customer SLA causes a 5% loss rate (36 RFQs/year), each worth ₹20 Lakh in annual sales at 12% contribution (₹2.40 Lakh/RFQ) = **₹86.40 Lakh/year**.

* **Total Baseline Annual Leakage**: **₹1.27 Crore/year**.

**CostForge Chakan** replaces fragile spreadsheets with a deterministic multi-volume costing engine, effective-dated Rate Masters with immutable quote snapshots, provenance-tagged AI RFQ intake with human-in-the-loop conflict resolution, and role-based commercial governance.

## Key Features & 7-Screen Architecture

| Screen / Module | Core Capabilities | 
| ----- | ----- | 
| **1. Master RFQ Register & SLA Tracker** | Real-time working-day SLA countdown badges (`≤ 4.0d` target vs `9.0d` baseline), pipeline valuation in ₹ Lakhs, assigned estimator filters, and structured `Won` / `Lost` reason tracking. | 
| **2. AI RFQ Intake & Title-Block Extractor** | Parses incoming RFQ emails, Excel part schedules, and NDA-watermarked 2D CAD drawing title blocks. Displays per-field source citations, confidence badges, cross-document conflict alerts, and similarity-matched historical routings. | 
| **3. Part Costing Workbench** | Dense, aligned financial grid with tabular numerals (`JetBrains Mono`), live animated cost-share composition bar, swarf/flash scrap recovery credit, multi-op routing table, and side-by-side 3-volume pricing (`50%`, `100% Base`, `150%`) with separate 18% GST. | 
| **4. Versioned Rate Masters** | Single source of truth for Raw Material rates (`EN8`, `40Cr4 forging`, `20MnCr5`, `SAE8620`) and Machine Hour rates (`₹780–₹1,450/hr`) with effective dates (`RM-2026-Q4`, `RM-2026-Q3`, `RM-2026-Q1`). | 
| **5. Approvals & Routing Sign-Off** | Enforces the **> ₹25.00 Lakh Annual Value Sales Head Approval Gate** and **Plant Head** technical cycle-time verification before quote release. | 
| **6. PDF Quote & Open-Book Cost Breakup** | Printable A4 Tier-1 OEM open-book quotation with HSN `8708 99 00`, multi-volume unit schedule, Ex-Works price in ₹, separate 18% GST, locked Rate Snapshot ID, and signatory blocks. | 
| **7. Past Quotes (1,400 Rows) & Excel Import** | Instant search across 1,400+ historical Chakan quotes by material grade, gross weight envelope, or part family, with one-click routing cloning and legacy Excel batch ingestion. | 

## How the AI Part Works (And What Happens When AI Is Wrong or Unsure)

1. **Zero AI in Cost Math**: All piece-cost calculations use fixed, auditable deterministic formulas. AI is strictly confined to intake extraction and historical routing retrieval.

2. **Per-Field Provenance & Confidence Scores**: Every extracted field shows its source (`Drawing Title Block Box 4`, `Excel Col E`, `Email Body L9`) and confidence score (`0–100%`).

3. **Cross-Document Conflict Detection**: In scenario **`RFQ-2611-031 — Low-Confidence / Conflict Edge Case`**, where the Excel sheet specifies `EN8` while Drawing Note 2 specifies `40Cr4` and the scanned weight digit is blurred, confidence drops to **54%** and highlights a conflict warning.

4. **Mandatory Estimator Acceptance Gate**: "Accept All High-Confidence (≥90%)" skips uncertain fields. Both the UI and backend (`validate_quote_release()`) block quote approval and dispatch until every extracted field is explicitly accepted or overridden by an Estimator.

5. **Traceable Routing Suggestions**: Suggested routings cite the exact historical quote they came from (`QUOTE-2508-112`, `QUOTE-2504-067`, `QUOTE-2509-204`) and the similarity percentage.

## Verified Sample Data & Deterministic Cost Summary (`RM-2026-Q4`)

| RFQ No | Customer | Part Name | Material | Gross / Net Wt | Base Annual Vol | Cycle & Hour Rate | Net Material (₹/pc) | Conversion @ Base (₹/pc) | Ex-Works Price (₹/pc) | GST @ 18% (₹/pc) | Annual Value (Ex-GST) | 
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | 
| **RFQ-2611-014** | Company B (two-wheelers) | Rear wheel spindle | `EN8` | 0.61 / 0.48 kg | 180,000 | 3.2 min @ ₹850/hr | ₹43.84 | ₹45.42 | **₹111.40** | ₹20.05 | **₹200.52 L** *(> ₹25L Gate)* | 
| **RFQ-2611-019** | Company C (tractors) | Hydraulic lift arm | `40Cr4 forging` | 4.60 / 3.85 kg | 24,000 | 11.5 min @ ₹1,450/hr | ₹454.10 | ₹280.10 | **₹906.64** | ₹163.20 | **₹217.59 L** *(> ₹25L Gate)* | 
| **RFQ-2611-023** | Company D (drivetrains) | Gear blank | `20MnCr5` | 1.48 / 1.18 kg | 60,000 | 4.8 min @ ₹950/hr | ₹126.98 | ₹76.38 | **₹248.19** | ₹44.67 | **₹148.91 L** *(> ₹25L Gate)* | 

## Repository Structure

```
chakan_rfq_project/
├── backend/
│   ├── costing_engine.py              # Deterministic multi-volume math, rate snapshots & approval gates
│   ├── ai_intake.py                   # Conflict detection, material normalization & similarity matcher
│   └── server.py                      # HTTP JSON API & SQLite persistence server
├── frontend/
│   └── index.html                     # Self-contained 7-screen interactive web application
├── scripts/
│   └── seed_1400_quotes.py            # Generates 1,400 legacy quote rows for Excel/CSV import
├── sample_data/
│   └── legacy_1400_past_quotes.csv    # Seeded 1,400-row historical quote dataset
├── tests/
│   └── test_costing_and_governance.py # Automated unit test suite for math, rate locking & RBAC
├── Technical_Design_Document.pdf      # Architecture, data model, labeled assumptions & UI rationale
├── deployment.md                      # Step-by-step local run guide, env var names & demo logins
├── .env.example                       # Environment variable template (names only, zero secrets)
└── README.md                          # Project overview and quickstart guide

```

## Quickstart (Local & VS Code)

The backend uses Python 3's standard library (`sqlite3`, `http.server`, `unittest`) so you can run tests and start the server immediately with zero `pip install` steps.

### 1. macOS / Linux / Git Bash

```
cp .env.example .env
python3 scripts/seed_1400_quotes.py
PYTHONPATH=. python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 backend/server.py

```

### 2. Windows (PowerShell in VS Code)

```
Copy-Item .env.example .env
python scripts/seed_1400_quotes.py
$env:PYTHONPATH="."; python -m unittest discover -s tests -v
$env:PYTHONPATH="."; python backend/server.py

```

Open **`http://localhost:8000`** in your browser (or open `frontend/index.html` directly with VS Code Live Server).

## Demo Credentials & Role Personas

You can switch roles anytime using the **Signed in as** selector in the top header bar or verify credentials in the **Session & NDA Log** modal:

| Role | Name | Email | Password | Permissions | 
| ----- | ----- | ----- | ----- | ----- | 
| **Estimator** | Rajesh Kulkarni | `rajesh.kulkarni@companya-pune.in` | `ChakanEst#2026` | Verify AI intake fields, edit multi-volume costing, lock rate snapshots, submit for approval | 
| **Sales Head** | Vikram Joshi | `vikram.joshi@companya-pune.in` | `ChakanSales#2026` | Approve quotes > ₹25.00 Lakh annual value, adjust target margins, mark quotes Sent / Won / Lost | 
| **Plant Head** | Anand Shinde | `anand.shinde@companya-pune.in` | `ChakanPlant#2026` | Verify manufacturing routings, cycle times, and machine cell assignments | 
| **Managing Director** | S. Deshpande | `md@companya-pune.in` | `ChakanMD#2026` | Executive SLA & pipeline oversight, publish new Rate Master revisions | 

## Security & NDA Governance

* **No Secrets in Repository**: `.env` and SQLite `.db` files are excluded via `.gitignore`; `.env.example` contains variable names only.

* **Customer NDA Protection**: CAD drawings are restricted to named users with dynamic session watermarking and an immutable audit log, and AI extraction enforces zero-retention headers (`AI_ZERO_RETENTION_HEADER=true`) so customer drawings are never used for model training.