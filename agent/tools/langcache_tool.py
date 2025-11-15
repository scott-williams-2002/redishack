# tools/langcache_tool.py
from typing import Optional, Dict, List
import os

# LangGraph Tool Decorator and ToolNode
from langchain.tools import tool
from langgraph.prebuilt import ToolNode

# LangCache imports
from langcache import LangCache
from langcache.models import SearchStrategy

# ChatOpenAI for summarization
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


# initialize client (reads env vars)
lang_cache = LangCache(
    server_url=f"https://{os.getenv('LANGCACHE_HOST', '')}",
    cache_id=os.getenv('LANGCACHE_CACHE_ID', ''),
    api_key=os.getenv('LANGCACHE_API_KEY', '')
)


def _summarize_product_text_helper(product_text: str) -> str:
    """Helper function to summarize product text using ChatOpenAI.
    
    This is the core summarization logic that can be called directly
    or through the tool wrapper.
    
    Args:
        product_text: The full product description text to summarize
        
    Returns:
        A summarized version of the product text as a string.
    """
    try:
        model = ChatOpenAI(model="gpt-4o")
        
        prompt = (
            "Summarize the following product description into key points focusing on "
            "features, specifications, and benefits. Keep it concise and informative:\n\n"
            f"{product_text}"
        )
        
        response = model.invoke([HumanMessage(content=prompt)])
        summary = response.content if hasattr(response, 'content') else str(response)
        
        return summary
    except Exception as e:
        return f"Error summarizing product text: {str(e)}"


@tool
def summarize_product_text(product_text: str) -> str:
    """Summarize product page text into key points using AI.
    
    Takes product description text and generates a concise summary focusing on
    features, specifications, and benefits.
    
    Args:
        product_text: The full product description text to summarize
        
    Returns:
        A summarized version of the product text as a string.
    """
    return _summarize_product_text_helper(product_text)


@tool
def store_product(
    product_url: str,
    description: str,
    summary: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict:
    """Store product information in LangCache.
    
    Stores the product URL, description, and summary as three separate entries
    in LangCache. If summary is not provided, it will be automatically generated.
    
    Args:
        product_url: The URL of the product page
        description: The full product description text
        summary: Optional pre-generated summary. If None, will be auto-generated.
        user_id: Optional user identifier for filtering
        
    Returns:
        Dictionary containing the results of storing all three entries.
    """
    # Generate summary if not provided
    if summary is None:
        summary = _summarize_product_text_helper(description)
    
    # Prepare base attributes shared by all entries
    base_attributes = {"product_url": product_url}
    if user_id:
        base_attributes["user_id"] = user_id
    
    results = {}
    
    # Store URL entry
    url_attributes = {**base_attributes, "type": "product_url"}
    results["url_entry"] = lang_cache.set(
        prompt=f"product_url:{product_url[:50]}",
        response=product_url,
        attributes=url_attributes
    )
    
    # Store description entry
    desc_attributes = {**base_attributes, "type": "product_description"}
    results["description_entry"] = lang_cache.set(
        prompt=f"product_description:{product_url[:50]}:{description[:40]}",
        response=description,
        attributes=desc_attributes
    )
    
    # Store summary entry
    summary_attributes = {**base_attributes, "type": "product_summary"}
    results["summary_entry"] = lang_cache.set(
        prompt=f"product_summary:{product_url[:50]}:{summary[:40]}",
        response=summary,
        attributes=summary_attributes
    )
    
    return results


@tool
def get_products(
    query: str,
    user_id: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """Retrieve products from LangCache using semantic search for RAG.
    
    Searches across product summaries using semantic matching, with optional
    filtering by user_id. Returns products with their URLs, descriptions, and summaries.
    
    Args:
        query: Search query for semantic matching against product summaries
        user_id: Optional user identifier to filter results
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        List of product entries, each containing URL, description, and summary.
    """
    # Build attributes for filtering
    attributes = {"type": "product_summary"}
    if user_id:
        attributes["user_id"] = user_id
    
    # Search using semantic matching on summaries
    res = lang_cache.search(
        prompt=query,
        attributes=attributes,
        similarity_threshold=0.01,  # Low threshold to allow semantic matching
        search_strategies=[SearchStrategy.EXACT]  # Exact match on attributes, semantic on content
    )
    
    # Extract entries
    entries = res.get("entries", []) if isinstance(res, dict) else res
    
    if not entries:
        return []
    
    # Limit results
    summary_entries = entries[:limit]
    
    # For each summary entry, fetch the corresponding URL and description
    products = []
    for entry in summary_entries:
        product_url = entry.get("attributes", {}).get("product_url", "")
        if not product_url:
            continue
        
        # Fetch URL and description entries for this product
        url_attributes = {"product_url": product_url, "type": "product_url"}
        if user_id:
            url_attributes["user_id"] = user_id
            
        desc_attributes = {"product_url": product_url, "type": "product_description"}
        if user_id:
            desc_attributes["user_id"] = user_id
        
        # Get URL entry
        url_res = lang_cache.search(
            prompt=product_url,
            attributes=url_attributes,
            similarity_threshold=0.01,
            search_strategies=[SearchStrategy.EXACT]
        )
        url_entries = url_res.get("entries", []) if isinstance(url_res, dict) else url_res
        product_url_value = url_entries[0].get("response", product_url) if url_entries else product_url
        
        # Get description entry
        desc_res = lang_cache.search(
            prompt=f"description for {product_url}",
            attributes=desc_attributes,
            similarity_threshold=0.01,
            search_strategies=[SearchStrategy.EXACT]
        )
        desc_entries = desc_res.get("entries", []) if isinstance(desc_res, dict) else desc_res
        description = desc_entries[0].get("response", "") if desc_entries else ""
        
        # Combine into product result
        products.append({
            "url": product_url_value,
            "description": description,
            "summary": entry.get("response", ""),
            "score": entry.get("score", 0.0),
            "attributes": entry.get("attributes", {})
        })
    
    return products


def create_langcache_tool_node():
    """Factory returning a ToolNode wrapping the LangCache product tools.

    Keeps existing consumers (which expect a ToolNode instance) working.
    """
    return ToolNode(
        tools=[store_product, get_products, summarize_product_text]
    )
