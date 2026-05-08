import time
from fastapi import APIRouter, Request, HTTPException

from src.models.models import CompareRequest, WinnerResponse
from src.services.ai_service import (
    compare_models, judge_winner,
    DEFAULT_MODELS, AVAILABLE_MODELS
)

router = APIRouter(prefix="/api/llm-arena", tags=["LLM Arena"])

@router.get("/models")
async def list_models():
    return AVAILABLE_MODELS

@router.post("/compare")
async def run_comparison(request: Request, payload: CompareRequest):
    session = request.app.state.http_session
    models = payload.models or DEFAULT_MODELS
    start = time.time()
    result = await compare_models(models, session, payload.prompt)
    elapsed = time.time() - start
    result["elapsed"] = round(elapsed, 2)

    # Сохраняем последний результат в состоянии приложения
    request.app.state.arena_last_results = result.get("results", [])
    return result

@router.post("/winner", response_model=WinnerResponse)
async def declare_winner(request: Request):
    results = getattr(request.app.state, "arena_last_results", [])
    if len(results) < 2:
        raise HTTPException(400, "Сначала запустите сравнение моделей")
    decision = judge_winner(results)
    return WinnerResponse(**decision)