import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.service.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = None


class ApprovalRequest(BaseModel):
    thread_id: str
    approve: bool


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    HTTP Entry point for the agentic chat.
    Delegates all business logic to AgentService.
    """
    try:
        async def event_generator():
            async for event_data in agent_service.stream_chat(request.message, request.thread_id):
                yield f"data: {event_data}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/approve")
async def approve_endpoint(request: ApprovalRequest):
    """
    HTTP Entry point to resume paused agent tasks.
    """
    if not request.approve:
        return {"status": "aborted", "thread_id": request.thread_id}

    try:
        result = await agent_service.approve_agent_action(request.thread_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))