# FinOps Guardian — First-Time Runbook

Follow these exact steps in order if you are installing and running FinOps Guardian for the very first time on a new machine.

## 1. Environment Configuration
Before any Python scripts can be run, the system needs access credentials for the PostgreSQL database and the LLM engine.

1. Ensure you have a `.env` file in the absolute root directory of your project (e.g., `/Users/ayushmali/Documents/finops-guardian-live/.env`).
2. The `.env` file **MUST** contain the following parameters:
   ```env
   # PostgreSQL database connection (e.g., Neon DB)
   DATABASE_URL=postgresql://<user>:<password>@<host>/<dbname>?sslmode=require
   
   # LLM API Key (Depends on what your wrapper supports)
   OPENAI_API_KEY=sk-... 
   # or
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## 2. Initialize the Database Schema
The database starts empty. We must create the exact table structures (`anomaly_logs` and `forecast_results`) so the ML engine has somewhere to write its data.

**Run the Setup Script:**
```bash
python db/setup_db.py
```
*Expected Output: Confirms that tables have been successfully created or verified in PostgreSQL.*

## 3. Train the AI Models (Artifact Generation)
The pipeline needs pre-trained models to execute anomalies safely. The `optimized_training.py` script will run the Optuna loops, tune the AI models against your historical data, and save the configurations into the `ml/artifacts/` folder.

**Run the Optimizer:**
```bash
# We use --fast-dev to prevent the 30-trial loop from taking hours during initial setup.
python ml/optimized_training.py --fast-dev
```
*Expected Output: You will see Optuna tuning sequences printing to the terminal. It should end with "Pipeline Completed Successfully." and populate the `ml/artifacts` folder.*

## 4. Execute the Intelligence Pipeline (ETL)
Now that the database exists and the models are trained, we run the primary background engine. This script extracts the billing data, runs the anomaly and forecast inferences using the saved artifacts, asks the LLM for root causes, and dumps everything to the database.

**Run the Inference Engine:**
```bash
python ml/run_pipeline_once.py
```
*Expected Output: "Pipeline completed successfully. Check database."*

## 5. Launch the Executive Dashboard
With data firmly planted in PostgreSQL, you can launch the read-only Streamlit user interface. 

**Start Streamlit:**
```bash
streamlit run dashboard/app.py
```

*This will automatically pop open a browser tab at `http://localhost:8501`, rendering your entire FinOps Guardian environment.*

---

### Routine Operation
Once you have completed steps 1–3, you **never** need to run them again unless you want to recalibrate the AI models. 

For routine daily updates, you only need to run:
1. `python ml/run_pipeline_once.py` (simulating a daily job)
2. `streamlit run dashboard/app.py`
