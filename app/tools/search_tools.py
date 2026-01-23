from langchain_core.tools import tool
from app.schemas.workflow.tool_schemas import WebSearchSchema
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

# Load again here just in case this module is loaded first
load_dotenv()

# We initialize the base tool from LangChain
# k=3 means it will bring the top 3 most relevant results
tavily_tool = TavilySearchResults(k=3)

@tool(args_schema=WebSearchSchema)
def web_search_tool(query: str) -> str:
    """
    Search the internet for real-time information with Tavily, news, or specific facts.
    Use this tool when the information is not in your internal knowledge
    or when you need up-to-date data.
    """
    # This is a wrapper to ensure it follows our architectural patterns
    try:
        results = tavily_tool.invoke({"query": query})
        return str(results)
    except Exception as e:
        return f"Search failed: {str(e)}"