from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state of the agent, representing the current conversation
    and the history of thoughts and actions.
    """
    # add_messages allows us to append new messages to the history
    # instead of overwriting it
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # We will use this to track token usage across the lifecycle
    total_tokens: int