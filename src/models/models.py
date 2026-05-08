from pydantic import BaseModel
from typing import Optional

class CompareRequest(BaseModel):
    models: Optional[list[str]] = None
    prompt: Optional[str] = None

class WinnerResponse(BaseModel):
    winners: list[str]
    losers: list[str]
    message: str