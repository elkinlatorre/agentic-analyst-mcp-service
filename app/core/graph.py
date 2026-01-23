from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.core.agent import AgentManager
from app.schemas.workflow.agent_state import AgentState
from app.core.mcp_manager import MCPManager

# 1. Instanciar managers (sin lógica de nodos aún)
manager = AgentManager()
mcp_manager = MCPManager()


def should_continue(state: AgentState):
    if state.get("total_tokens", 0) > 7000:
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


# --- INFRAESTRUCTURA ---
DB_PATH = "checkpoints.db"
saver_context = AsyncSqliteSaver.from_conn_string(DB_PATH)
app_graph = None


async def initialize_graph():
    """
    Inicializa MCP, actualiza herramientas y compila el grafo dinámicamente.
    """
    global app_graph

    # 1. Conexión MCP
    await mcp_manager.connect()

    # 2. Obtener herramientas remotas y actualizar el Manager
    remote_tools = await mcp_manager.get_mcp_tools()
    manager.update_tools(remote_tools)

    # 3. Definir el Grafo AHORA que tenemos todas las herramientas
    workflow = StateGraph(AgentState)

    # 4. Añadir Nodos
    workflow.add_node("agent", manager.call_model)
    workflow.add_node("tools", ToolNode(manager.all_tools))  # Aquí ya van las 8 herramientas
    workflow.add_node("human_approval", human_approval)

    # 5. Definir Flujo (Edges)
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

    # 6. Compilación con Checkpointer
    checkpointer = await saver_context.__aenter__()
    app_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"]
    )

    print("--- [GRAPH] Compiled successfully with local and MCP tools ---")
    return app_graph