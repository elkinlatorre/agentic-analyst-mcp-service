import sys
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from contextlib import AsyncExitStack
from pydantic import create_model



class MCPManager:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session = None

        # 1. Resolve paths
        base_path = Path(__file__).parent.parent.parent
        db_path = base_path / "external_data.db"

        # 2. Find the executable in the virtual environment
        # In Windows, pip installs the script as mcp-server-sqlite.exe in venv/Scripts/
        venv_path = Path(sys.prefix)
        if os.name == "nt":  # Windows
            mcp_executable = venv_path / "Scripts" / "mcp-server-sqlite.exe"
        else:  # Linux/Mac
            mcp_executable = venv_path / "bin" / "mcp-server-sqlite"

        # 3. Configure parameters pointing to the executable
        self.server_params = StdioServerParameters(
            command=str(mcp_executable),
            args=["--db-path", str(db_path)],
            env=os.environ.copy()
        )

    async def connect(self):
        """Initializes the connection with the MCP Server."""
        try:
            # We use the exit_stack to manage the lifecycle of both streams and session
            read_stream, write_stream = await self.exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            # Start the MCP initialization handshake
            await self.session.initialize()
            print("--- [MCP] Connected to SQLite Server successfully ---")
        except Exception as e:
            print(f"--- [MCP ERROR] Failed to connect: {str(e)} ---")
            raise e

    async def get_mcp_tools(self) -> list:
        if not self.session:
            return []

        mcp_tools = await self.session.list_tools()
        langchain_tools = []

        for tool in mcp_tools.tools:
            name = tool.name
            description = tool.description
            input_schema = tool.inputSchema

            properties = input_schema.get("properties", {})
            DynamicArgsModel = create_model(
                f"{name}Args",
                **{k: (object, ...) for k in properties.keys()}
            )

            async def tool_wrapper(name=name, **kwargs):
                """
                We use **kwargs to force LangChain to pass a dictionary
                of named arguments instead of a positional string.
                """
                print(f"DEBUG - Executing MCP Tool '{name}' with args: {kwargs}")
                # MCP is expecting dict
                result = await self.session.call_tool(name, kwargs)

                combined_output = "\n".join(
                    [content.text for content in result.content if hasattr(content, 'text')]
                )
                return combined_output

            langchain_tools.append(
                StructuredTool.from_function(
                    name=name,
                    description=description,
                    func=None,
                    coroutine=tool_wrapper,
                    args_schema=DynamicArgsModel
                )
            )
        return langchain_tools

    async def disconnect(self):
        """Closes the connection gracefully."""
        await self.exit_stack.aclose()