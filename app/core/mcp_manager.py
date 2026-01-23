import os
import yaml

from pathlib import Path
from typing import Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from contextlib import AsyncExitStack
from pydantic import create_model
from app.core.security import SQLSecurityValidator
from pydantic import Field #

class MCPHubManager:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: List[ClientSession] = []
        self.config = self._load_config()

    def _load_config(self) -> dict:
        config_path = Path(__file__).parent.parent.parent / "mcp_config.yaml"
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    async def connect(self):
        """Conecta a todos los servidores definidos en el YAML."""
        for name, settings in self.config["mcp_servers"].items():
            try:
                server_params = StdioServerParameters(
                    command=settings["command"],
                    args=settings["args"],
                    env=os.environ.copy()
                )

                # Cada servidor tiene su propio stream y sesión
                read_stream, write_stream = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )

                await session.initialize()
                self.sessions.append(session)
                print(f"--- [MCP HUB] Connected to {name} ---")
            except Exception as e:
                print(f"--- [MCP HUB ERROR] Failed to connect to {name}: {e} ---")

    async def get_all_mcp_tools(self) -> list:
        all_langchain_tools = []

        # Metadata we want the model to know WITHOUT putting it in the system prompt
        db_context = (
            "Target table: 'products'. "
            "Columns: [id (INT), name (TEXT), price_in_cents (INT), stock (INT)]. "
            "Note: price_in_cents is (dollars * 100)."
        )

        for session in self.sessions:
            mcp_tools = await session.list_tools()

            for tool in mcp_tools.tools:
                name = tool.name
                description = tool.description
                input_schema = tool.inputSchema
                properties = tool.inputSchema.get("properties", {})

                # Here is the trick: We inject the context into the Pydantic field description
                fields = {}
                for k in properties.keys():
                    field_desc = properties[k].get("description", "")
                    if "query" in k or "sql" in k:
                        # We append the DB context to the argument's own description
                        field_desc = f"{field_desc}. {db_context}".strip()

                    fields[k] = (object, Field(..., description=field_desc))

                DynamicArgsModel = create_model(f"{name}Args", **fields)

                async def tool_wrapper(name=name, session=session, **kwargs):

                    # 1. Extract query/sql from kwargs
                    query = kwargs.get("query") or kwargs.get("sql")

                    # 2. Security Validation
                    if query and not SQLSecurityValidator.validate_query(str(query)):
                        return SQLSecurityValidator.get_security_error_message()

                    # 3. Execution
                    result = await session.call_tool(name, kwargs)
                    combined_output = "\n".join(
                        [content.text for content in result.content if hasattr(content, 'text')]
                    )
                    return combined_output

                all_langchain_tools.append(
                    StructuredTool.from_function(
                        name=name,
                        description=description,
                        coroutine=tool_wrapper,
                        args_schema=DynamicArgsModel
                    )
                )
        return all_langchain_tools

    async def disconnect(self):
        await self.exit_stack.aclose()