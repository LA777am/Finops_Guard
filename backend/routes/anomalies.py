from fastapi import APIRouter, Query
from backend.services.data_service import get_anomalies
from backend.schemas import AnomalyResponse

router = APIRouter()

@router.get("/", response_model=AnomalyResponse)
def fetch_anomalies(
    service: str = Query(None),
    provider: str = Query(None)
):
    data = get_anomalies(service, provider)
    return {
        "count": len(data),
        "data": data
    }