from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Anomaly(BaseModel):
    id: int
    date: datetime
    provider: str
    service_category: str
    team: str
    cost_usd: float
    is_anomaly: bool
    severity_label: Optional[str]
    severity_score: Optional[float]
    root_cause: Optional[str]
    llm_insight: Optional[str]
    recommended_action: Optional[str]
    estimated_savings: Optional[str]
    model_votes: Optional[int]


class AnomalyResponse(BaseModel):
    count: int
    data: List[Anomaly]


class Forecast(BaseModel):
    id: int
    date: datetime
    provider: str
    service_category: str
    team: str
    forecast_50: float
    forecast_90: float
    forecast_10: float
    horizon_days: int


class ForecastResponse(BaseModel):
    count: int
    data: List[Forecast]


class Metric(BaseModel):
    id: int
    model_name: str
    f1_score: float
    precision_score: float
    recall_score: float
    mape: float
    created_at: datetime