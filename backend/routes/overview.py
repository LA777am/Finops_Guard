from fastapi import APIRouter
from backend.services.data_service import get_anomalies

router = APIRouter()
from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_anomalies: int
    p0_critical: int
    p1_high: int
    high_severity: int
    medium_severity: int
    low_severity: int
@router.get("/", response_model=OverviewResponse)
def get_overview():
    data = get_anomalies()

    # 🔥 Ensure correct format
    if isinstance(data, list):
        records = data
    else:
        records = data.to_dict(orient="records")

    total = sum(1 for d in records if d.get("is_anomaly") == True)

    p0 = sum(1 for d in records if d.get("priority") == "P0 - Critical")
    p1 = sum(1 for d in records if d.get("priority") == "P1 - High")
    high = sum(1 for d in records if d.get("severity_label") == "high")
    medium = sum(1 for d in records if d.get("severity_label") == "medium")
    low = sum(1 for d in records if d.get("severity_label") == "low")
    print(type(data))
    print(data[:2])
    return {
        "total_anomalies": total,
        "p0_critical": p0,
        "p1_high": p1,
        "high_severity": high,
        "medium_severity": medium,
        "low_severity": low
    }