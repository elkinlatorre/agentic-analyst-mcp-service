from pydantic import BaseModel, Field
from typing import Optional, List

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str = Field(..., example="No pending actions found for this session.")

class StreamResponse(BaseModel):
    """Schema representing a single chunk of data in the stream."""
    thread_id: str
    content: str
    node: str
    status: str
    next_step: Optional[List[str]] = None

class ApprovalResponse(BaseModel):
    """Response after an approval action."""
    status: str = Field(..., example="success")
    thread_id: str
    agent_response: str
    message: Optional[str] = None