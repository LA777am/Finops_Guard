# FinOps Guardian — Technical Documentation

## 1. System Overview
**FinOps Guardian** is an enterprise-grade, autonomous cloud cost intelligence platform. It replaces traditional, reactionary cost observability dashboards by deploying a unified 3-layer AI ensemble to detect anomalies, applying LLM-driven attribution to isolate the root cause, and executing probability-based forecasts to catch budget breaches before they occur.

Instead of heavy client-side processing, FinOps Guardian completely decouples the heavy inference pipeline from the user interface. ML models are executed via a Python pipeline, heavily parallelized and tuned, which sinks conclusions entirely into a **PostgreSQL (Neon) Database**. The Streamlit-powered dashboard serves strictly as a high-performance, real-time read-replica visualizer.

---

## 2. Platform Architecture

The platform operates on a batch-intelligence paradigm.
```text
[ Data Ingestion ] → [ Pipeline ETL ] → [ Multi-Layer AI ] → [ PostgreSQL ] → [ Streamlit UI ]
```

### Tech Stack
- **Database:** PostgreSQL (Neon DB). B-tree indexing enabling instant analytical reads on highly dimensional anomaly logic.
- **Frontend / UI:** Streamlit with deeply overridden CSS styling, pure Plotly (`plotly.graph_objects`) for GPU-accelerated interactive visualizations.
- **AI / ML Layer:** PyTorch (LSTM), Scikit-Learn (Isolation Forest), Prophet (Time-Series Extrapolation), LightGBM.
- **Optimization:** Optuna (Hyperparameter search space tuning).

---

## 3. The Intelligence Engines

### A. 3-Layer Ensemble Anomaly Detection
To prevent adversarial noise from triggering mass false alerts inside high-velocity cloud systems, Guardian enforces a strict ensemble agreement boundary.

1. **Z-Score (Statistical Baseline):** Rapidly scans for extreme deviations against rolling distributions. Detects immediate massive spikes.
2. **Isolation Forest (Machine Learning):** Computes isolation distance against multidimensional billing features (utilization metrics, weekend vs. weekday usage).
3. **LSTM Autoencoder (Deep Learning):** Analyzes chronological embeddings. Capable of memorizing seasonal cloud load schedules and flagging temporal shifts.

**Voting Mechanism:** An event is only declared an anomaly if it crosses a consensus threshold (e.g., `model_votes >= 2`). 

### B. Impact & Priority Logic
Not all anomalies matter. A 1,000% spike on a $1 compute instance is irrelevant noise. Guardian forces financial gravity onto the anomaly detection metrics.
* `severity_score` = Computed natively via ratio of agreeing models.
* `impact_score` = `severity_score` × `cost_usd`

**Priority Action Funnel:**
- **P0 Critical:** Impact > $3,000 (Requires Immediate Action)
- **P1 High:** Impact > $1,500 
- **P2 Medium:** Impact > $500
- **P3 Low:** Noise. 

### C. Automated Root Cause Analysis (LLM Integration)
Instead of forcing engineers to hunt through Azure or AWS consoles, Guardian processes high-priority flags against an LLM-attributed dictionary, providing:
- **Root Cause:** Identical architectural trigger mechanisms.
- **Insight:** Security/FinOps reasoning.
- **Estimated Savings:** Probabilistic unspent dollar amounts recovered upon execution.
- **Recommended Action:** Exact commands or steps (e.g., *Audit CDN usage*).

### D. Probabilistic Forecasting Engine
Maps cost trajectories extending out to 90 days.
- Uses **Prophet** for deep seasonality matching across massive date variances.
- Maps **P10 (Best Case)**, **P50 (Trajectory)**, and **P90 (Worst Case)** confidence interval bands.
- Validates the next 30 days against the allocated frontend budget thresholds and assigns Risk Labels (`HIGH RISK`, `LOW RISK`).

---

## 4. The Database Layer

To guarantee sub-second load times on the visual frontend, the entire data model lives inside optimized tables in PostgreSQL.

### Core Tables & Schemas
**1. `anomaly_logs`**
Holds absolute truth for historical flags.
`date`, `provider`, `service_category`, `team`, `cost_usd`, `is_anomaly`, `severity_label`, `severity_score`, `root_cause`, `llm_insight`, `recommended_action`, `estimated_savings`, `model_votes`, `impact_score`, `priority`

**2. `forecast_results`**
Tracks trajectory metrics bounds.
`date`, `provider`, `service_category`, `team`, `forecast_50`, `forecast_90`, `forecast_10`, `horizon_days`

### Query Interface
The `db/database.py` utilizes custom cursor pools and explicit retrieval architectures:
- `fetch_anomalies(limit=10000)`
- `fetch_forecasts(limit=5000)`
- `fetch_metrics()` 

All query execution is bound to `@st.cache_data` on the frontend, enforcing lightning-fast memory retrieval and blocking any redundant server hits during dashboard filter adjustments.

---

## 5. Decision Executive Dashboard

Run strictly via `dashboard/app.py`, the user interface is completely injected with sophisticated HTML/CSS overrides masking stock limitations, providing a completely Fintech-grade operating panel.

**Core Interactions:**
- **Progressive Hydration:** Bypasses UI freezing via Streamlit placeholders, allowing the user to view the layout instantly while complex PostgreSQL queries resolve in the center spinner natively.
- **Cross-Service Correlation Analysis:** Automatically merges timestamp indexes in the anomaly matrix, allowing teams to see if an AWS RDS spike mathematically corresponds perfectly with an AWS EC2 spike natively—identifying architectural domino effects.
- **Data Exporting:** All grids natively translate into localized `.csv` dumps for external reporting tools. 

---
*Created by: Team Catalyst Core | Tic Tech Toe '26*
