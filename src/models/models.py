# src/models/models.py
from pydantic import BaseModel
from typing import Optional

class CompareRequest(BaseModel):
    models: Optional[list[str]] = None
    prompt: Optional[str] = None

class ModelEvidence(BaseModel):
    model: str
    found_rule: bool
    snippet: str = ""

class WinnerResponse(BaseModel):
    winners: list[str]
    losers: list[str]
    message: str
    evidence: list[ModelEvidence] = []