# FinOps Guardian — ML & Deep Learning Architecture Review

## 1. Intelligence Philosophy
FinOps Guardian abandons the flawed paradigm of static alerting thresholds (e.g., "Alert if cost > $500"). Cloud native environments exhibit volatile scaling patterns, complex seasonalities, and multithreaded variances. To combat this, the system deploys a decoupled, **Segment-Based Ensemble Architecture**.

**Segment Isolation:** The system groups data natively by `[service_category, team]`. ML models are not trained globally against the noisy aggregate environment. We spin up bespoke, localized AI models strictly assigned to individual cost centers, allowing the ML algorithms to perfectly match the microscopic heartbeat of each specific infrastructure component.

---

## 2. Hyperparameter Optimization Framework (Optuna)
All ML architectures within FinOps Guardian are dynamically tuned across search spaces via **Optuna**. We do not rely on hardcoded defaults. Since cloud cost data shifts over time, the system uses a stochastic search loop inside `ml/optimized_training.py` during execution.

### Tuning Paradigm
- **Trials Run:** 30 parallel trials generated per service node.
- **Optimization Algorithms:** TPE (Tree-structured Parzen Estimator).
- **Core Strategy:** Models output decision boundaries or reconstruction errors natively. Optuna sweeps empirical quantiles (e.g., 80th-99.9th percentile score distributions) and computes strict **F1-Scores** across validation holds, rejecting any trial that inflates false positives.

---

## 3. The 3-Layer AI Ensemble

No single algorithm can perfectly map financial anomaly patterns. Guardian stacks 4 independent modeling strategies, scaling their vectors down via `MinMaxScaler(0,1)` natively, and forces Optuna to learn the optimal weighted vote-ratio per service.

### A. Statistical Baseline: Z-Score Volatility
- **Objective:** Measure gross absolute cost velocity against strict rolling historical metrics.
- **Features Handled:** `rolling_mean_7`, `rolling_std_7`.
- **Why it’s here:** Protects the AI pipeline from missing obvious, absolute monetary explosions. Captures the extreme outliers.

### B. Machine Learning I: Isolation Forest (Pattern Shifts)
- **Objective:** Detects structural drifts against global usage boundaries.
- **Optuna Search Space:** 
  - `n_estimators`: Integers between [100, 400]
  - `max_samples`: Float between [0.5, 1.0] (Prevents overfitting on extreme variances).
  - `contamination`: Float between [0.01, 0.15] (Bounds the percent of data we allow the system to assume anomalous natively).
  - `max_features`: Subspace feature selection [0.5, 1.0].
- **Calibrated Objective:** Maximizes localized F1 extraction limits.

### C. Machine Learning II: One-Class SVM (Boundary Deflection)
- **Objective:** Generates non-linear boundary spheres around nominal usage.
- **Optuna Search Space:** 
  - `kernel`: Strictly `rbf` (Radial Basis Function) to handle complex financial hyperplanes.
  - `nu`: Allowed margin of error/anomalies within the train scope [0.01, 0.2].
  - `gamma`: Categorical sweep over ['scale', 'auto'].

### D. Deep Learning: LSTM Autoencoder (Temporal Embedding)
- **Objective:** Memorizes sequences of temporal scaling (e.g., "The RDS database always scales up exactly at 9:00 AM on Monday, and rests at 5:00 PM Friday").
- **Architecture:** PyTorch `nn.LSTM` Encoder-Decoder paradigm.
- **Training Flow:** Uses Sequence length blocks (`seq_len = 14`). We embed `cost_usd`, `rolling_mean_7`, `pct_change_1d` into the tensor graph.
- **Optuna Search Space:**
  - `hidden_dim`: Sweeps block depths of [16, 64].
  - `num_layers`: Maps 1 to 2 dense recurrent layers natively.
  - `learning_rate`: Logarithmic uniform distribution between [1e-4, 1e-2] over Adam.
  - `epochs`: 10-25 passes with Mean Square Error (MSE) loss extraction constraint.
- **Inference logic:** The model generates reconstructed features. We extract the absolute deviation (MSE loss per row). Optuna sweeps percentiles [95, 96, 97, 98, 99] of the error distributions to find the absolute F1-Score maximized threshold.

### E. The Meta-Ensemble Classifier
Rather than treating each model equally, we feed the normalized outputs back into Optuna for final configuration natively.
- Optuna floats variables `w_z`, `w_if`, `w_svm`, `w_lstm` bounding between 0.0 to 1.0. 
- It assesses linearly blending the normalized anomaly scores of the entire pipeline, maximizing precision constraints dynamically. The final weights are dumped strictly into the database for the pipeline processor wrapper.

---

## 4. Probabilistic Forecasting Engine

To compute accurate 30-day and 90-day trajectory mappings for predictive budget signals, Guardian fuses two opposing regression topologies.

### A. LightGBM (Feature Gradient Boosting)
- **Objective:** Maps non-linear combinations of usage to prevent naive extrapolation.
- **Optuna Tuning Metric:** Minimizes Mean Absolute Percentage Error (MAPE). 
- **Search Space:**
  - `num_leaves`: [15, 63] (Controls native complexity bounding).
  - `learning_rate`: Log-uniform boundaries [0.01, 0.1].
  - `n_estimators`: Deep search [100, 500].
  - `subsample` & `colsample_bytree`: Enforces randomized mapping to suppress over-fitting gradients.
- **Early-Stopping Rounds:** 20 frames implemented perfectly to drop dead-end trials.

### B. Meta Prophet Extrapolation
- **Objective:** Extracts pure time-series structural seasonalities exclusively built by Facebook's architecture.
- **Optuna Tuning Protocol:**
  - `changepoint_prior_scale`: [0.01, 0.5] (Determines exactly how flexible the model is when reacting to huge sudden changes in financial trajectories).
  - `seasonality_prior_scale`: [1.0, 10.0].
  - `weekly_seasonality`: Strictly enforced to map Friday night/Weekend drop-offs in infrastructure logic. 

---

## 5. Artifact Retention & Portability
All Optuna JSON states, PyTorch `lstm.pth` weights arrays, and Scikit-Learn models are cached and serialized directly to `./ml/artifacts/{segment_id}` natively.

This enables the pipeline execution (`run_pipeline_once.py`) to bypass retraining natively on standard runs—acting exactly as a production-grade inference handler pulling intelligence from PostgreSQL.
