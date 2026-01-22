import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.graph import app_graph
from langchain_core.messages import HumanMessage
from fastapi.responses import StreamingResponse

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "total_tokens": 0
        }
        # Note: We use the synchronous invoke for simplicity now
        result = app_graph.invoke(inputs)

        final_message = result["messages"][-1].content
        tokens_used = result["total_tokens"]

        return {
            "status": "success",
            "agent_response": final_message,
            "usage": {"total_tokens": tokens_used}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Endpoint that streams the agent's thought process and final response.
    """
    try:
        async def event_generator():
            inputs = {
                "messages": [HumanMessage(content=request.message)],
                "total_tokens": 0
            }

            # Use astream to get events in real time
            async for event in app_graph.astream(inputs, stream_mode="values"):
                if event:
                    last_message = event["messages"][-1]
                    tokens = event.get("total_tokens", 0)

                    data = {
                        "node": "agent_execution",  # LangGraph values mode returns the full state
                        "content": last_message.content,
                        "total_tokens": tokens
                    }
                    yield f"data: {json.dumps(data)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))