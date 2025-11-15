"""
Product marketing analyzer tool for detecting manipulative marketing tactics.
"""

from langchain.tools import tool
from typing import Optional


@tool
def analyze_product_marketing(
    product_name: str,
    product_link: str,
    image_url: str,
    description: str,
    suspected_tactics: str,
) -> dict:
    """
    Analyze a product for manipulative marketing tactics and return structured data
    for rendering a custom UI component in CopilotKit.
    
    Args:
        product_name: Name of the product
        product_link: Link to the product page
        image_url: URL of the product image
        description: Description of the product
        suspected_tactics: Comma-separated list of suspected manipulative tactics
    
    Returns:
        A dictionary with product analysis data including manipulative tactics
        and a question for the user to confirm or deny the findings.
    """
    
    # Parse the suspected tactics
    tactics_list = [tactic.strip() for tactic in suspected_tactics.split(',') if tactic.strip()]
    
    # Generate a question for the user
    user_question = (
        f"Do you agree that '{product_name}' uses these manipulative marketing tactics? "
        "Please review the product page and let me know if you notice any additional tactics or if you disagree with my analysis."
    )
    
    # Return the structured data that will be passed to the frontend component
    return {
        "productName": product_name,
        "productLink": product_link,
        "imageUrl": image_url,
        "description": description,
        "manipulativeTactics": "|".join(tactics_list),  # Use pipe delimiter for easy splitting in frontend
        "userQuestion": user_question,
    }
