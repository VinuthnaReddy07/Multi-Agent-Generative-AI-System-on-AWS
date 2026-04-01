"""Menu agent for restaurant menu queries and information retrieval."""
# menu_agent.py
import json
import os
from datetime import datetime

import boto3
from strands import Agent, tool  # pylint: disable=import-error
from strands.models import BedrockModel  # pylint: disable=import-error

MENU_KNOWLEDGE_BASE_ID = os.environ.get("MENU_KNOWLEDGE_BASE_ID", "")
REGION = os.environ.get("REGION", "us-east-1")
# Use foundation model directly
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)

# === Tools ===
@tool(name="menu_kb_retrieve",
      description="A tool to retrieve data from restaurant menu knowledge base")
def menu_kb_retrieve(query: str) -> str:
    """Search the menu knowledge base using retrieve_and_generate."""
    if not MENU_KNOWLEDGE_BASE_ID:
        return "Menu knowledge base is not configured. Please contact support."

    params = {
        "input": {"text": query},
        "retrieveAndGenerateConfiguration": {
          "type": "KNOWLEDGE_BASE",
          "knowledgeBaseConfiguration": {
              "knowledgeBaseId": MENU_KNOWLEDGE_BASE_ID,
              "modelArn": MODEL_ARN,
              "retrievalConfiguration": {
                  "vectorSearchConfiguration": {
                      "numberOfResults": 7,
                      "overrideSearchType": "HYBRID"
                  }
              }
          }
      }
    }
    try:
        response = bedrock_runtime.retrieve_and_generate(**params)
        return response.get("output", {}).get(
            "text", "No relevant information found in the knowledge base.")
    except (KeyError, ValueError, ConnectionError) as e:
        return f"Failed to retrieve information: {str(e)}"

@tool(name="get_menu")
def get_menu() -> dict:
    """Fetch menu JSON from S3 and return as parsed object."""
    bucket = os.environ.get("WORKSHOP_S3_BUCKET",
                           os.environ.get("S3_BUCKET_NAME", ""))
    key = "menu/menu_records.json"
    s3 = boto3.client("s3")
    data = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    return json.loads(data)

@tool(name="check_seasonal_availability")
def check_seasonal_availability(item_name: str) -> str:
    """Check if a seasonal item is currently available based on the current month."""
    try:
        menu_data = get_menu()
        current_month = datetime.now().month
        
        # Extract base item name (remove size and customizations)
        base_item_name = item_name.lower()
        # Remove common size words
        for size in ['small', 'medium', 'large', 'sized']:
            base_item_name = base_item_name.replace(size, '').strip()
        # Remove common customizations
        for custom in ['with oat milk', 'with almond milk', 'with soy milk', 'oat milk', 'almond milk', 'soy milk']:
            base_item_name = base_item_name.replace(custom, '').strip()
        
        # Find the item in the menu by checking exact matches or item_id matches
        for item in menu_data:
            menu_item_name = item["name"].lower()
            item_id = item["item_id"].lower()
            # Check for exact name match or item_id match, or if the base name closely matches
            if (base_item_name == menu_item_name or 
                base_item_name == item_id or
                base_item_name.replace('_', ' ') == menu_item_name or
                menu_item_name.replace(' ', '_') == base_item_name):
                # Check if it's a seasonal item
                if item.get("attributes_json", {}).get("seasonal", False):
                    season_months = item.get("attributes_json", {}).get("season_months", [])
                    if current_month in season_months:
                        return f"{item['name']} is available now during its seasonal period."
                    # Find the next available month
                    next_months = [m for m in season_months if m > current_month]
                    if next_months:
                        next_month = min(next_months)
                    else:
                        next_month = min(season_months)  # Next year

                    month_names = {
                        1: "January", 2: "February", 3: "March", 4: "April",
                        5: "May", 6: "June", 7: "July", 8: "August",
                        9: "September", 10: "October", 11: "November", 12: "December"
                    }

                    return (f"{item['name']} is a seasonal item and is not currently available. "
                            f"Please come back in {month_names[next_month]} when it returns to our menu!")
                return f"{item['name']} is available year-round with customizations like size and milk options."

        return f"Base item for '{item_name}' is not found on our menu."
    except (KeyError, ValueError, ConnectionError) as e:
        return f"Unable to check seasonal availability: {str(e)}"

# === Agent Definition ===

menu_agent = Agent(
    model=BedrockModel(
        model_id='arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0'
    ),
    system_prompt="""
        - You are 'Menu Assistant' for AnyCompany Coffee Shop, an expert in our menu.
        - Always wrap your answer in <answer> tags.
        - Give 1-2 sentences answers only.
        - Only answer using information obtained using available tools. Do not use your own information.
        - If errors occur, acknowledge it politely.
        - When you receive a query, determine if the question is about restaurant menu.
        - For queries not related to menu, respond with 'Sorry, I cannot answer this question'.
        - For menu-related queries, first fetch S3 menu data using the get_menu tool.
        - IMPORTANT: For any specific item inquiry, use the check_seasonal_availability tool to verify if seasonal items are currently available.
        - IMPORTANT: When customers ask about items with sizes (small/medium/large) or milk customizations (oat milk, almond milk, etc.), check the base item availability first.
        - IMPORTANT: Only confirm items are available for ordering if they exist in the menu data AND are currently in season (for seasonal items).
        - If a seasonal item is not currently available, inform the customer when it will return.
        - For regular menu items like Latte, Mocha, etc., they are available in all sizes (small, medium, large) and with various milk options
        - Only for menu-related queries that can not be answered from S3 menu data, you can check the menu knowledge base using menu_kb_retrieve tool.
        - If nothing relevant is found using either the get_menu or menu_kb_retrieve tools, clearly state the item is not available on the menu.
        """,
    tools=[menu_kb_retrieve, get_menu, check_seasonal_availability],
)
