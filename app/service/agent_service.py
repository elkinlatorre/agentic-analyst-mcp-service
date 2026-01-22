import uuid
import json
from typing import AsyncGenerator, Optional
from langchain_core.messages import HumanMessage
from app.core import graph  # Import the module to access the global app_graph


class AgentService:
    @staticmethod
    def generate_thread_id() -> str:
        return str(uuid.uuid4())

    async def stream_chat(self, message: str, thread_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        current_thread_id = thread_id or self.generate_thread_id()
        config = {"configurable": {"thread_id": current_thread_id}}

        inputs = {
            "messages": [HumanMessage(content=message)],
            "total_tokens": 0
        }

        # Accessing the globally initialized graph
        async for event in graph.app_graph.astream(inputs, config, stream_mode="values"):
            if event:
                last_message = event["messages"][-1]
                yield json.dumps({
                    "thread_id": current_thread_id,
                    "content": last_message.content,
                    "node": "agent_execution",
                    "status": "in_progress"
                })

        snapshot = await graph.app_graph.aget_state(config)
        if snapshot.next:
            yield json.dumps({
                "thread_id": current_thread_id,
                "status": "waiting_approval",
                "next_step": snapshot.next
            })

    async def approve_agent_action(self, thread_id: str) -> dict:
        config = {"configurable": {"thread_id": thread_id}}

        snapshot = await graph.app_graph.aget_state(config)
        if not snapshot.next:
            return {"status": "error", "message": "No pending actions found."}

        # Resume with None as input
        result = await graph.app_graph.ainvoke(None, config)
        return {
            "status": "success",
            "thread_id": thread_id,
            "agent_response": result["messages"][-1].content
        }