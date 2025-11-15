"""
LangGraph + CopilotKit agent with Redis Cloud long-term memory + Web Search.
"""

from tools.tavily_agent import create_tavily_search_tool_node, tavily_search
from tools.product_analyzer import analyze_product_marketing

from typing import Any, List
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
import redis
import ssl
import os

# ----------------------------------------------------------------------
# Redis Cloud Long-Term Memory
# ----------------------------------------------------------------------

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,           # REQUIRED for Redis Cloud
    ssl_cert_reqs=None,
    decode_responses=True
)

# ----------------------------------------------------------------------
# Agent State
# ----------------------------------------------------------------------

class AgentState(MessagesState):
    shopping_profile: dict = {}
    tools: List[Any]

# ----------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------


@tool
def update_shopping_profile(user_id: str, category: str = "", search_term: str = ""):
    """Update Redis Cloud shopping profile."""
    if category:
        redis_client.sadd(f"user:{user_id}:categories", category)
    if search_term:
        redis_client.rpush(f"user:{user_id}:search_history", search_term)
    return "Shopping profile updated."


@tool
def get_shopping_profile(user_id: str):
    """Retrieve the long-term profile from Redis Cloud."""
    categories = list(redis_client.smembers(f"user:{user_id}:categories"))
    history = redis_client.lrange(f"user:{user_id}:search_history", 0, -1)
    return {
        "categories": categories,
        "search_history": history,
    }


backend_tools = [
    update_shopping_profile,
    get_shopping_profile,
    tavily_search,
    analyze_product_marketing,
]

backend_tool_names = [tool.name for tool in backend_tools]

# ----------------------------------------------------------------------
# Chat Node (ReAct)
# ----------------------------------------------------------------------

async def chat_node(state: AgentState, config: RunnableConfig):
    model = ChatOpenAI(model="gpt-4o")

    model_with_tools = model.bind_tools(
        [
            *state.get("tools", []), 
            *backend_tools,         # Tavily included
        ],
        parallel_tool_calls=False
    )

    system_message = SystemMessage(
        content=(
            "You are a shopping assistant agent with long-term memory stored in Redis. "
            "Your primary goal is to analyze products for manipulative marketing tactics. "
            "When the user asks you to analyze a product, you MUST use the `analyze_product_marketing` tool. "
            "You must provide realistic values for all tool parameters, including a list of suspected tactics. "
            "When relevant, use the `tavily_search` tool to perform deep research web searches. "
            f"Current shopping profile: {state.get('shopping_profile', {})}"
        )
    )

    response = await model_with_tools.ainvoke(
        [system_message, *state["messages"]],
        config
    )

    if route_to_tool_node(response):
        return Command(
            goto="tool_node",
            update={"messages": [response]},
        )

    return Command(
        goto=END,
        update={"messages": [response]},
    )


def route_to_tool_node(response: BaseMessage):
    tool_calls = getattr(response, "tool_calls", None)
    if not tool_calls:
        return False

    for tc in tool_calls:
        if tc.get("name") in backend_tool_names:
            return True
    return False


# ----------------------------------------------------------------------
# LangGraph Workflow
# ----------------------------------------------------------------------

websearch_tool = create_tavily_search_tool_node()

workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)
workflow.add_node("tool_node", ToolNode(tools=backend_tools))


workflow.add_edge("tool_node", "chat_node")
workflow.set_entry_point("chat_node")

graph = workflow.compile()
