from typing import Any

from pydantic import BaseModel


class CommandRequest(BaseModel):
    text: str
    session_token: str | None = None


class CommandResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    latency_ms: int
    action_data: dict[str, Any] | None = None
    session_token: str | None = None


class CommandLogResponse(BaseModel):
    raw_input: str
    detected_intent: str
    confidence_score: float
    status: str
    created_at: str

    class Config:
        from_attributes = True
