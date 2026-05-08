# src/schemas/schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional, Any


class CompareRequest(BaseModel):
    models: Optional[list[str]] = None
    prompt: Optional[str] = None

class WinnerRequest(BaseModel):
    results: list[dict]

class ArenaResultResponse(BaseModel):
    id: int
    model1: str
    model2: str
    winner: str | None
    message: str
    evidence: list[Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)