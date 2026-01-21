from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.core.agent import AgentManager
from app.schemas.agent_state import AgentState

# Initialize our Manager
manager = AgentManager()


def should_continue(state: AgentState):
    """
    Conditional edge to determine if we should go to tools or finish.
    """

    # --- SAFETY GUARD: TOKEN LIMIT ---
    # If we exceed 5000 tokens, we stop to prevent massive costs
    if state.get("total_tokens", 0) > 7000:
        print("!!! SAFETY ALERT: Token limit exceeded. Stopping agent.")
        return END

    messages = state['messages']
    last_message = messages[-1]

    # If the LLM made a tool call, we move to the "tools" node
    if last_message.tool_calls:
        return "tools"

    # Otherwise, we stop
    return END


# 1. Define the Graph
workflow = StateGraph(AgentState)

# 2. Define the Nodes
# 'agent' node: The brain (Manager.call_model)
workflow.add_node("agent", manager.call_model)

# 'tools' node: The hands (Executes the tools)
tool_node = ToolNode(manager.tools)
workflow.add_node("tools", tool_node)

# 3. Define the Edges
# The entry point is the agent
workflow.set_entry_point("agent")

# After the agent, we decide if we go to tools or END
workflow.add_conditional_edges(
    "agent",
    should_continue,
)

# After tools are executed, we ALWAYS go back to the agent
# to let it "observe" the result and think again (Cycle)
workflow.add_edge("tools", "agent")

# 4. Compile the Graph
# This is the final object we will call from our API
app_graph = workflow.compile()