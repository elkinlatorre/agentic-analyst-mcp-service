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
from pydantic import Field


class MCPHubManager:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session_configs: Dict[ClientSession, dict] = {}
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
                self.session_configs[session] = settings
            except Exception as e:
                print(f"--- [MCP HUB ERROR] Failed to connect to {name}: {e} ---")

    async def _mcp_tool_executor(self, session: ClientSession, name: str, **kwargs):
        """Validador de seguridad y ejecutor."""
        query = kwargs.get("query") or kwargs.get("sql")
        if query and not SQLSecurityValidator.validate_query(str(query)):
            return SQLSecurityValidator.get_security_error_message()

        result = await session.call_tool(name, kwargs)
        return "\n".join([c.text for c in result.content if hasattr(c, 'text')])

    async def get_all_mcp_tools(self) -> list:
        all_langchain_tools = []

        for session in self.sessions:
            # Recuperamos la metadata específica de este servidor desde el YAML
            server_settings = self.session_configs.get(session, {})
            custom_context = server_settings.get("custom_metadata", {}).get("db_context", "")

            mcp_tools = await session.list_tools()
            for tool in mcp_tools.tools:
                # Inyectamos el contexto solo si la herramienta parece ser de SQL o si es relevante
                fields = {}
                for k, v in tool.inputSchema.get("properties", {}).items():
                    desc = v.get("description", "")
                    if custom_context and any(kw in k.lower() for kw in ["query", "sql", "url"]):
                        desc = f"{desc}. {custom_context}"
                    fields[k] = (object, Field(..., description=desc))

                args_model = create_model(f"{tool.name}Args", **fields)

                # Definimos el runner con closure para capturar la sesión correcta
                async def runner(tool_name=tool.name, tool_session=session, **kwargs):
                    return await self._mcp_tool_executor(tool_session, tool_name, **kwargs)

                all_langchain_tools.append(
                    StructuredTool.from_function(
                        name=tool.name,
                        description=tool.description,
                        coroutine=runner,
                        args_schema=args_model
                    )
                )
        return all_langchain_tools

    async def disconnect(self):
        await self.exit_stack.aclose()