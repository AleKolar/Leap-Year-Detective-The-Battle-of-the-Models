from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from src.models.models import CompareRequest, WinnerResponse
from src.services.ai_service import (
    run_arena_comparison, judge_winner,
    DEFAULT_MODELS, AVAILABLE_MODELS
)
from src.database.database import get_db
from src.models.db_models import ArenaResult

router = APIRouter(prefix="/api/llm-arena", tags=["LLM Arena"])

@router.get("/models")
async def list_models():
    return AVAILABLE_MODELS

@router.post("/compare")
async def run_comparison(
    request: Request,
    payload: CompareRequest,
    db: Session = Depends(get_db)
):
    session = request.app.state.http_session
    models = payload.models or DEFAULT_MODELS
    result = await run_arena_comparison(models, session, payload.prompt)

    battle = ArenaResult(
        model1=models[0],
        model2=models[1],
        winner=None, # определяется на состязании
        message="Сравнение завершено",
        evidence=result.get("results", [])
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)

    result["arena_result_id"] = battle.id
    return result

@router.post("/winner", response_model=WinnerResponse)
async def declare_winner(
    request: Request,
    db: Session = Depends(get_db)
):
    last_battle = db.query(ArenaResult).order_by(ArenaResult.id.desc()).first()
    if not last_battle:
        raise HTTPException(400, "Сначала запустите сравнение моделей.")

    results = last_battle.evidence
    if not isinstance(results, list) or len(results) < 2:
        raise HTTPException(400, "Некорректные данные битвы в БД")

    decision = judge_winner(results)
    last_battle.winner = decision["winners"][0] if decision["winners"] else "draw"
    last_battle.message = decision["message"]
    db.commit()

    return WinnerResponse(**decision)

@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    battles = db.query(ArenaResult).order_by(ArenaResult.id.desc()).limit(10).all()
    return battles