from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Initial chat request with optional thread continuity."""
    message: str = Field(..., example="Search for NVIDIA price and save to nvidia.txt")
    thread_id: Optional[str] = Field(None, example="550e8400-e29b-41d4-a716-446655440000")

class ApprovalRequest(BaseModel):
    """Request to approve or reject a pending agent action."""
    thread_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    approve: bool = Field(..., example=True)