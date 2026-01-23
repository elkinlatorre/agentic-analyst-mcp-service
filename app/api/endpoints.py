from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.service.agent_service import AgentService
from app.schemas.api.requests import ChatRequest, ApprovalRequest
from app.schemas.api.responses import StreamResponse, ApprovalResponse, ErrorResponse

router = APIRouter()
agent_service = AgentService()


@router.post(
    "/chat/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "model": StreamResponse,
            "description": "Successful stream start",
            "content": {
                "text/event-stream": {"schema": {"$ref": "#/components/schemas/StreamResponse"}}
            }
        },
        500: {"model": ErrorResponse}
    }
)
async def chat_stream_endpoint(request: ChatRequest):
    """
    Entry point for agentic chat with streaming and HITL support.
    """
    try:
        async def event_generator():
            async for event_data in agent_service.stream_chat(request.message, request.thread_id):
                yield f"data: {event_data}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        # Note: In streaming, errors after the response starts are handled differently,
        # but this catches initial setup errors.
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/chat/approve",
    response_model=ApprovalResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Approve or reject a pending agent action"
)
async def approve_endpoint(request: ApprovalRequest):
    """
    Resume the agent execution after a 'human_approval' breakpoint.
    """
    if not request.approve:
        return ApprovalResponse(
            status="aborted",
            thread_id=request.thread_id,
            agent_response="N/A",
            message="Action was rejected by the user."
        )

    try:
        result = await agent_service.approve_agent_action(request.thread_id)

        # Handle business logic errors from the service layer
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return ApprovalResponse(
            status="success",
            thread_id=request.thread_id,
            agent_response=result["agent_response"],
            message="Action approved and executed successfully."
        )
    except HTTPException as he:
        # Re-raise known HTTP exceptions
        raise he
    except Exception as e:
        # Catch-all for unexpected crashes
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")