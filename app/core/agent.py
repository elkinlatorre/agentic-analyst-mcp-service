import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.schemas.workflow.agent_state import AgentState
from langchain_core.messages import SystemMessage
from app.tools.file_tools import save_report_to_disk
from app.tools.search_tools import web_search_tool

load_dotenv()


class AgentManager:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.static_tools = [save_report_to_disk, web_search_tool]
        self.all_tools = self.static_tools
        self.llm_with_tools = self.llm.bind_tools(self.all_tools)
        # Load the prompt from YAML during initialization
        self.system_prompt = self._load_prompt()

    def update_tools(self, mcp_tools: list):
        """Updates the LLM binding with both local and MCP tools."""
        self.all_tools = self.static_tools + mcp_tools
        self.llm_with_tools = self.llm.bind_tools(self.all_tools)
        print(f"--- [DEBUG] Agent tools updated. Total: {len(self.all_tools)} ---")

    def _load_prompt(self) -> str:
        """Loads the system prompt from a YAML file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "analyst_v1.yaml"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['system_prompt']

    def call_model(self, state: AgentState):
        MAX_TOKENS = 7000
        SAFE_MARGIN = 2000

        current_usage = state.get("total_tokens", 0)

        if current_usage > (MAX_TOKENS - SAFE_MARGIN):
            from langchain_core.messages import AIMessage
            print(f"--- [DEBUG] Stopping early. Usage: {current_usage} ---")
            return {
                "messages": [AIMessage(content="STOP: High token usage detected. Finishing task now.")],
                "total_tokens": current_usage
            }

        messages = state['messages']

        # Inject the System Prompt loaded from YAML
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system_prompt)] + messages

        response = self.llm_with_tools.invoke(messages)

        usage = response.response_metadata.get("token_usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        return {
            "messages": [response],
            "total_tokens": state.get("total_tokens", 0) + prompt_tokens + completion_tokens
        }