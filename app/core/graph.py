from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.core.agent import AgentManager
from app.schemas.workflow.agent_state import AgentState
from app.core.mcp_manager import MCPHubManager

# 1. Managers instances
manager = AgentManager()
mcp_hub = MCPHubManager()


def should_continue(state: AgentState):
    if state.get("total_tokens", 0) > 30000:
        return END

    messages = state['messages']
    last_message = messages[-1]

    if not last_message.tool_calls:
        return END

    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "save_report_to_disk":
            return "human_approval"

    return "tools"


def human_approval(state: AgentState):
    pass


# --- INFRASTRUCTURE ---
DB_PATH = "checkpoints.db"
saver_context = AsyncSqliteSaver.from_conn_string(DB_PATH)
app_graph = None


async def initialize_graph():
    """
    It initializes MCP, updates the tools, and compiles the graph dynamically.
    """
    global app_graph

    # 1. MCP Connection
    await mcp_hub.connect()

    # 2. Get remote tools and update Manager
    remote_tools = await mcp_hub.get_all_mcp_tools()
    manager.update_tools(remote_tools)

    # 3. Initilize graph
    workflow = StateGraph(AgentState)

    # 4. Adding Nodes
    workflow.add_node("agent", manager.call_model)
    workflow.add_node("tools", ToolNode(manager.all_tools))
    workflow.add_node("human_approval", human_approval)

    # 5. Edges
    workflow.set_entry_point("agent")

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

    # 6. Compile Checkpointer
    checkpointer = await saver_context.__aenter__()
    app_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"]
    )

    print("--- [GRAPH] Compiled successfully with local and MCP tools ---")
    return app_graph