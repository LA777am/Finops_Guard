from fastapi import FastAPI
from backend.routes import anomalies, forecasts, metrics, overview

app = FastAPI(title="FinOps Guardian API")

app.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])
app.include_router(forecasts.router, prefix="/forecasts", tags=["Forecasts"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
app.include_router(overview.router, prefix="/overview", tags=["Overview"])


@app.get("/")
def root():
    return {"status": "API is running"}