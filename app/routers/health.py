# routes/health.py
from fastapi import APIRouter, Response

router = APIRouter()

@router.get("/health")
@router.head("/health")
async def health_check():
    return Response(status_code=200)