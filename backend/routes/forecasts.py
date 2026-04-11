from fastapi import APIRouter, Query
from backend.services.data_service import get_forecasts
from backend.schemas import ForecastResponse

router = APIRouter()

@router.get("/", response_model=ForecastResponse)
def fetch_forecasts(service: str = Query(None)):
    data = get_forecasts(service)
    return {
        "count": len(data),
        "data": data
    }