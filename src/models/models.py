# src/models/models.py
from datetime import datetime

from pydantic import BaseModel
from typing import Optional

class CompareRequest(BaseModel):
    models: Optional[list[str]] = None
    prompt: Optional[str] = None

class ModelEvidence(BaseModel):
    model: str
    found_rule: bool
    snippet: str = ""
    num_asserts: int = 0
    has_1900: bool = False
    has_2000: bool = False
    has_2100: bool = False
    has_negative: bool = False
    has_typical_leap: bool = False
    has_typical_common: bool = False
    has_assert_messages: bool = False
    coverage_points: int = 0

class WinnerResponse(BaseModel):
    winners: list[str]
    losers: list[str]
    message: str
    evidence: list[ModelEvidence] = []

class BattleHistoryResponse(BaseModel):
    id: int
    model1: str
    model2: str
    winner: Optional[str] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True