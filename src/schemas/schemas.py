# src/schemas/schemas.py
from pydantic import BaseModel
from typing import Optional

class CompareRequest(BaseModel):
    models: Optional[list[str]] = None
    prompt: Optional[str] = None

class WinnerRequest(BaseModel):
    results: list[dict]