from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.core.agent import AgentManager
from app.schemas.agent_state import AgentState

# Initialize our Manager
manager = AgentManager()


def should_continue(state: AgentState):
    """
    Conditional edge to determine if we should go to tools or finish.
    """
    # --- SAFETY GUARD: TOKEN LIMIT ---
    if state.get("total_tokens", 0) > 7000:
        print("!!! SAFETY ALERT: Token limit exceeded. Stopping agent.")
        return END

    messages = state['messages']
    last_message = messages[-1]

    # If no tool has been call, agent finish
    if not last_message.tool_calls:
        return END

    # If tool 'save_report_to_disk', force human approval
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "save_report_to_disk":
            return "human_approval"  # Forzamos el paso por el nodo de pausa

    return "tools"


def human_approval(state: AgentState):
    """
    A 'ghost' node that does nothing, but serves as a breakpoint specifically for sensitive actions.
    """
    pass


# 1. Define the Graph
workflow = StateGraph(AgentState)

# 2. Define the Nodes
workflow.add_node("agent", manager.call_model)
workflow.add_node("tools", ToolNode(manager.tools))
workflow.add_node("human_approval", human_approval)

# 3. Define the Edges
workflow.set_entry_point("agent")

# Agent decide: ¿End? ¿Tools? o ¿Human approval?
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "human_approval": "human_approval",
        END: END
    }
)

workflow.add_edge("human_approval", "tools")
workflow.add_edge("tools", "agent")

# --- DATABASE CONNECTION MANAGEMENT ---
# We create the saver instance here
DB_PATH = "checkpoints.db"
# This is the context manager
saver_context = AsyncSqliteSaver.from_conn_string(DB_PATH)

# We will define app_graph as None and compile it inside the lifespan
app_graph = None

async def initialize_graph():
    """
    Function to be called during FastAPI lifespan to correctly
    initialize the graph with an active checkpointer.
    """
    global app_graph
    # Entering the context manager to get the ACTUAL saver object
    checkpointer = await saver_context.__aenter__()
    app_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"]
    )
    return app_graph