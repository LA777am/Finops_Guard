<div align="center">
  <h1>🛡️ FinOps Guardian</h1>
  <p><strong>Autonomous Cloud Cost Intelligence & Remediation Engine</strong></p>
  <sub>Replace reactive observability with predictive, explainable, and autonomous cloud financial intelligence.</sub>
</div>

---

## ⚡ Beyond Dashboards: A Decision Engine

Modern cloud environments suffer from uncontrolled resource sprawl, delayed detection of billing anomalies, and weak forecasting. Traditional observability platforms tell you *what* happened days after the invoice is cut.

**FinOps Guardian** is a proactive decision intelligence system. Operating across multi-cloud environments, it abstracts raw billing data through a highly tuned 3-Layer AI ensemble to detect anomalies instantly, uses LLM-driven attribution to explain *why* they happened, and leverages LightGBM/Prophet to forecast trajectory before the budget breaks.

---

## 🧬 Core Intelligence Capabilities

### 1. ⚙️ Multi-Cloud Unification Taxonomy
Ingests and normalizes unstructured billing data from **AWS, Azure, and GCP** into a standardized telemetry format. Expenditures are categorized into `Compute`, `Storage`, `Networking`, and `Managed Services` to allow seamless cross-provider correlation.

### 2. 🧠 3-Layer Ensemble Anomaly Detection 
Instead of relying on rigid thresholds, Guardian utilizes a highly optimized voting ensemble to neutralize false positives while detecting complex structural drift.

| Layer | Architecture | Objective |
|-------|-------------|-----------|
| **Statistical** | `Z-Score` | Baseline variance & abrupt spike detection. |
| **Machine Learning** | `Isolation Forest` | Multidimensional pattern shifts against normal usage. |
| **Deep Learning** | `LSTM Autoencoder` | Chronological and temporal behavior embeddings. |

*Final trigger requires a majority vote (≥ 2 models consensus).*

### 3. 🎯 Advanced Risk & Priority Engine
Financial anomalies are explicitly calculated against relative monetary impact, preventing engineering teams from wasting time on low-cost noise. 

```text
severity_score = model_votes / 3
impact_score   = severity_score × cost_usd
```

| Priority | Impact Trigger | Routing Action |
|----------|----------------|----------------|
| **P0 - Critical** | Impact > $3,000 | Immediate intervention required. |
| **P1 - High**     | Impact > $1,500 | High urgency review pipeline. |
| **P2 - Medium**   | Impact > $500   | Monitor trend closely. |
| **P3 - Low**      | Impact < $500   | Informational logging. |

### 4. 💬 LLM-Driven Root Cause Attribution
Raw anomalies are sterile. FinOps Guardian enriches every anomalous event natively with actionable context:
- 📌 **Root Cause:** Identifies the architectural source.
- 🧾 **Insight Reasoning:** Explains the deviation logically.
- 🛠️ **Recommended Action:** Exactly what to terminate, resize, or audit.
- 💰 **Estimated Savings:** Hard dollar projections for remediation.

> *Example: "Unexpected data transfer spike → Misconfigured external routing → Audit CDN usage & redirect VPC → Expected Savings $1000+"*

### 5. 📈 Multi-Horizon Forecasting Engine
Predicts future spend distributions across **7, 30, and 90-day** horizons.
Guardian utilizes **Prophet** for seasonal time-series extrapolation and **LightGBM** to evaluate feature-driven dependencies, generating robust **P10, P50, and P90** confidence intervals. 

### 6. 🚨 Predictive Budget Breach Routing
Constantly maps the 90-day probability distributions against active thresholds. By calculating the likelihood of spending > budget, it isolates overspends and issues preemptive triggers *before* the infrastructure burns cash.

---

## 🏗️ System Architecture

FinOps Guardian abstracts heavy ML processing completely away from the frontend layer to guarantee instant performance.

```text
[ Raw Billing Data ] → [ Data Engineering Pivot ] → [ ML Training & Inference Pipeline ]
                                                                ↓
[ Streamlit Read-Only UI ] ← [ Neon PostgreSQL DB (Source of Truth) ]
```

### The Data Model
**Anomalies Schema**
`date` | `service_category` | `provider` | `team` | `cost_usd` | `is_anomaly` | `severity_label` | `severity_score` | `impact_score` | `priority` | `root_cause` | `llm_insight` | `recommended_action` | `estimated_savings` | `model_votes` 

**Forecasts Schema**
`date` | `service_category` | `forecast_10` | `forecast_50` | `forecast_90` | `horizon_days`

---

## ⚙️ Getting Started

**1. Run the Intelligence Pipeline (Background Computations)**
*This loads the synthetic billing data, executes all ML/DL models via Optuna tuning, and syncs conclusions safely onto PostgreSQL.*
```bash
python ml/run_pipeline_once.py
```

**2. Launch the Decision Executive Interface**
*Instantly pull from the database cache into the Streamlit ecosystem.*
```bash
streamlit run dashboard/app.py
```

---

## 🧠 Design Philosophy

1. **Ensemble > Single Model:** Combining methodologies prevents adversarial system noise from disrupting alerts.
2. **Explainability > Black Box:** AI has no value without attribution. We enforce SHAP and Linguistic derivations.
3. **Prediction > Reaction:** You shouldn't manage costs; you should steer forecasts.
4. **Impact > Noise:** We mute tiny fractional anomalies if the dollar-value impact is trivial, saving engineer fatigue.

---

<p align="center">
  <em>Cloud cost is not a monitoring problem. It is a decision problem. FinOps Guardian turns raw data into automated decisions.</em>
</p>
<p align="center">
  <sub>Building intelligent, performant systems for high-scale enterprise operations.</sub>
</p>
