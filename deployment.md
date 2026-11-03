# Deployment & Reviewer Guide (`deployment.md`)

**Project**: CostForge Chakan — RFQ-to-Quote Costing Web App (Company A, Chakan, Pune)  
**GitHub Repository URL**: `https://github.com/AdityaBansal0123/costforge-rfq-to-quote`   
**Live Deployed Application URL**: `https://costforge-chakan.up.railway.app` *(Self-contained interactive build also available in `frontend/index.html` / `chakan_rfq_costing_app.html`)*

## 1. Local Setup & Execution (Step-by-Step)

### Prerequisites
- **Python**: `>= 3.11` (uses standard library `sqlite3`, `http.server`, and `unittest` for zero-friction local execution; optional FastAPI/Uvicorn production runner)
- **Git**: `>= 2.30`
- **Modern Desktop Browser**: Chrome, Edge, or Firefox (optimized for 1280px–1920px estimator monitors and responsive down to 375px mobile width)

### Step 1: Clone the Repository
```bash
git clone https://github.com/AdityaBansal0123/costforge-rfq-to-quote.git
cd costforge-rfq-to-quote
```

### Step 2: Configure Environment Variables
Copy the environment template to `.env` (no external secret keys are required to run the seeded deterministic engine and local AI intake simulator):
```bash
cp .env.example .env
```

### Step 3: Seed the 1,400-Row Historical Quote Repository & SQLite Database
Generate the 1,400 legacy Excel/CSV quote rows (`sample_data/legacy_1400_past_quotes.csv`) and initialize the SQLite database with the 3 brief sample RFQs (`RFQ-2611-014`, `RFQ-2611-019`, `RFQ-2611-023`), versioned rate masters (`RM-2026-Q4`, `RM-2026-Q3`, `RM-2026-Q1`), and role accounts:
```bash
python3 scripts/seed_1400_quotes.py
```

### Step 4: Run the Automated Unit & Governance Test Suite
Verify the deterministic multi-volume costing formulas, rate master immutability, AI conflict detection, and `> ₹25.00 Lakh` Sales Head approval gate:
```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

### Step 5: Start the Application Server
```bash
PYTHONPATH=. python3 backend/server.py
```
Open **`http://localhost:8000`** in your browser.
- **Health Check Endpoint**: `GET http://localhost:8000/api/health`
- **RFQ JSON API Endpoint**: `GET http://localhost:8000/api/rfqs`
- **Direct Standalone UI Mode**: You can also open `frontend/index.html` (`chakan_rfq_costing_app.html`) directly in any browser with zero server setup.

## 2. Production Deployment Architecture & Environment Variables

### How It Is Deployed
1. **Application Tier**: Containerized via a single-stage `python:3.11-slim` Docker image deployed on **Railway / Render** (Mumbai `ap-south-1` region for `<35ms` latency to Company A's Chakan MIDC plant).
2. **Database & Storage Tier**:
   - **Transactional DB**: PostgreSQL 16 (production) / SQLite WAL mode (local development & single-node plant server) storing versioned rate snapshots, RFQ cost sheets, and immutable NDA audit logs.
   - **Drawing Object Storage**: Private S3-compatible bucket (`ap-south-1`) with pre-signed, short-lived URLs and dynamic named-user PDF watermarking.
3. **AI Extraction Tier (NDA Compliant)**:
   - Connects to an enterprise zero-data-retention Vision/Document extraction endpoint (`AI_ZERO_RETENTION_HEADER=true`) so customer CAD drawings under NDA are never retained or used for model training.

### Required Environment Variables (Names Only — Never Commit Values)
| Variable Name | Scope | Purpose |
| :--- | :--- | :--- |
| `APP_ENV` | Backend | Runtime environment (`development`, `staging`, `production`) |
| `PORT` | Backend | HTTP listener port (default `8000`) |
| `DATABASE_URL` | Backend / DB | Connection URI for SQLite or PostgreSQL database |
| `SESSION_SECRET_KEY` | Auth / Security | HMAC secret used to sign named-user session cookies |
| `JWT_SIGNING_KEY` | Auth / RBAC | Signing key for role-based access tokens (`estimator`, `sales_head`, `plant_head`, `md`) |
| `NDA_WATERMARK_SALT` | Security / Audit | Cryptographic salt for stamping named-user audit watermarks on drawing views |
| `AI_EXTRACTION_PROVIDER` | AI Intake | Provider selector (`azure_openai_zero_retention` or `local_deterministic`) |
| `AI_ENDPOINT_URL` | AI Intake | Private enterprise endpoint URL for title-block OCR and Excel/email parsing |
| `AI_API_KEY` | AI Intake | API credential for the enterprise zero-retention extraction endpoint |
| `AI_ZERO_RETENTION_HEADER` | NDA Governance | Enforces `x-ms-no-data-retention: true` on all extraction calls |
| `SALES_HEAD_APPROVAL_THRESHOLD_INR` | Commercial Policy | Annual contract value threshold requiring Sales Head approval (`2500000` = ₹25 Lakh) |
| `DEFAULT_GST_RATE_PCT` | Tax Compliance | Standard GST percentage shown separately on quotes (`18.0`) |
| `SLA_TARGET_WORKING_DAYS` | Operations | Target turnaround SLA in working days (`4.0`) |

## 3. Demo Login Details for the Reviewer

The application includes an instant **Signed-in Role Switcher** in the top navigation bar as well as a **Session & NDA Audit Log** modal so reviewers can test all four personas without re-typing passwords. For full-stack login verification, use the following seeded accounts:

| Role Persona | Name | Demo Email / Username | Demo Password | Key Capabilities to Test |
| :--- | :--- | :--- | :--- | :--- |
| **Senior Estimator** | Rajesh Kulkarni | `rajesh.kulkarni@companya-pune.in` | `ChakanEst#2026` | Run AI RFQ Intake (Tab 2), accept/override low-confidence OCR fields, apply past-part routing suggestions, adjust multi-volume costing (Tab 3), submit quotes for approval |
| **Sales Head** | Vikram Joshi | `vikram.joshi@companya-pune.in` | `ChakanSales#2026` | Approve quotes exceeding **₹25.00 Lakh** annual value (Tab 5), review margin % vs 12% target, release PDF Quote (Tab 6), mark RFQs Won/Lost with reason |
| **Plant Head** | Anand Shinde | `anand.shinde@companya-pune.in` | `ChakanPlant#2026` | Verify process routings, cycle times (min), setup times, and machine cell assignments (`CNC-TURN-CELL`, `FORGE-VMC-HEAVY`, `GEAR-TURN-HOB`) |
| **Managing Director** | S. Deshpande | `md@companya-pune.in` | `ChakanMD#2026` | Monitor plant-wide turnaround SLA (2.8d vs 4.0d target), pipeline value, and publish effective-dated Rate Master revisions (Tab 4) |

## 4. Recommended 3-Minute Reviewer Walkthrough
1. **RFQ Register (Tab 1)**: Inspect the 3 seeded brief RFQs (`RFQ-2611-014` Rear wheel spindle, `RFQ-2611-019` Hydraulic lift arm, `RFQ-2611-023` Gear blank) plus context RFQs showing `< ₹25L` auto-clearance (`RFQ-2611-027`), historical `Won` (`RFQ-2610-089`), and `Lost` due to late 9-day reply (`RFQ-2610-074`).
2. **AI Intake & Mistake Handling (Tab 2)**: Switch the scenario dropdown to **`RFQ-2611-031 — Low-Confidence / Conflict Edge Case`** to see how the app flags a material conflict (`Excel: EN8` vs `Drawing Note: 40Cr4` at `54%` confidence) and blocks quote approval until the estimator explicitly accepts or overrides the value. Click **Apply Suggested Routing** to pull operations from historical quote `QUOTE-2508-112`.
3. **Part Costing Workbench (Tab 3)**: Review the dense, aligned 3-volume costing table (`50%`, `100% Base`, `150%`), net material cost after 90% swarf scrap recovery, setup amortization, and separate 18% GST.
4. **Versioned Rate Masters (Tab 4)**: Click **+ Publish New Rate Master Revision** (`RM-2026-NOV`) and verify that existing quotes locked to `RM-2026-Q4` and `RM-2026-Q3` retain their exact historical rates.
5. **Approval Gate & Printable PDF Quote (Tabs 5 & 6)**: Switch role to **Sales Head (`Vikram Joshi`)**, approve `RFQ-2611-014` (`₹200.52 Lakh/yr > ₹25L gate`), and preview/print the Tier-1 open-book PDF quotation in Tab 6.
6. **Past Quotes & 1,400-Row Excel Import (Tab 7)**: Click **Import Legacy Excel Quotes (Simulate 1,400-Row Batch)** and filter historical parts by material grade and weight envelope.
