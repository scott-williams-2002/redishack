# tools/tavily_websearch.py
from typing import Optional, List, Dict
import os

# LangGraph Tool Decorator and ToolNode
from langchain.tools import tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from tavily import TavilyClient


class TavilySearchInput(BaseModel):
    query: str = Field(..., description="User search query")
    depth: str = Field(
        default="advanced",
        description="Search depth: default | basic | advanced. Use 'advanced' for deep research."
    )
    include_images: bool = Field(
        default=False,
        description="Whether to include images in the Tavily response."
    )
    include_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to restrict search to."
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to never search."
    )
    max_results: int = Field(
        default=8,
        description="Maximum number of result objects to return."
    )


@tool
def tavily_search(
    query: str,
    depth: str = "advanced",
    include_images: bool = False,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    max_results: int = 8,
) -> Dict:
    """Perform a Tavily web search and return the structured response.

    This is a simple function-style tool (decorated with `@tool`) so it can
    be passed directly to LangChain-style tool runners or wrapped in a
    `ToolNode` if needed.
    """

    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY missing from environment")

    client = TavilyClient(api_key=tavily_api_key)

    options = {
        "max_results": max_results,
        "include_images": include_images,
        "search_depth": depth,
    }
    if include_domains:
        options["include_domains"] = include_domains
    if exclude_domains:
        options["exclude_domains"] = exclude_domains

    try:
        return client.search(query=query, **options)
    except Exception as e:
        return {"error": f"Tavily SDK call failed: {str(e)}", "query": query}


def create_tavily_search_tool_node():
    """Compatibility factory returning a ToolNode wrapping the function tool.

    Keeps existing consumers (which expect a ToolNode instance) working.
    """
    return ToolNode(
        name="web_search",
        tools=[tavily_search]
    )
