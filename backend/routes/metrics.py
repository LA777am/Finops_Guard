from fastapi import APIRouter
from backend.services.data_service import get_metrics
from backend.schemas import Metric
from typing import List

router = APIRouter()

@router.get("/", response_model=List[Metric])
def fetch_metrics():
    return get_metrics()