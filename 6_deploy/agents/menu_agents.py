# menu_agent.py
import os
import json
import boto3
from strands import Agent, tool
from strands.models import BedrockModel

MENU_KNOWLEDGE_BASE_ID = os.environ["MENU_KNOWLEDGE_BASE_ID"]
REGION = os.environ["REGION"]
MODEL_ARN = os.environ["MODEL_ARN"]

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)

# === Tools ===
@tool(name="menu_kb_retrieve", description="A tool to retrieve data from restaurant menu knowledge base")
def menu_kb_retrieve(query: str) -> str:
    """Search the menu knowledge base using retrieve_and_generate."""
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
        return response.get("output", {}).get("text", "No relevant information found in the knowledge base.")
    except Exception as e:
        return f"Failed to retrieve information: {str(e)}"

@tool(name="get_menu")
def get_menu() -> dict:
    """Fetch menu JSON from S3 and return as parsed object."""
    bucket = os.environ["S3_BUCKET_NAME"]
    key = "menu/menu_records.json"
    s3 = boto3.client("s3")
    data = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    return json.loads(data)

@tool(name="calculate_order_total", description="Calculate total cost based on business pricing rules. Expected input format:items: [{\"type\": \"drink|bagel|donut\", \"size\": \"small|medium|large\", \"customizations\": [\"extra_shot\", \"oat_milk\"]}")
def calculate_order_total(items: list) -> dict:
    """
    Calculate total cost based on business pricing rules:
    - Drinks: $3 (small), $4 (medium), $5 (large) + $1 per customization
    - Bagels: $4.5 each
    - Donuts: $2.5 each
    """
    print(items)
    try:
        # Initialize total_cost as a number (float for decimal values).
        total_cost = 0.0

        for item in items:
            if item["type"] == "drink":
                # Calculate drink price directly.
                base_price = {"small": 3, "medium": 4, "large": 5}[item["size"].lower()]
                customization_cost = len(item.get("customizations", [])) * 1
                total_cost += base_price + customization_cost
            elif item["type"] == "bagel":
                # Add bagel price directly to the total.
                total_cost += 4.5
            elif item["type"] == "donut":
                # Add donut price directly to the total.
                total_cost += 2.5
        
        # Return the final calculated total, formatted as a currency string.
        return {"total_cost": f"${total_cost:.2f}"}
    except Exception as e:
        return {"error": str(e)}

# === Agent Definition ===

menu_agent = Agent(
    model=BedrockModel(model_id=os.environ["MODEL_ID"]),
    system_prompt="""
        - You are 'Menu Assistant', an expert in restaurant menus.
        - Always wrap your answer in <answer> tags.
        - Give 1-2 sentences answers only.
        - Only answer using information obtained using available tools. Do not use your own information.
        - If errors occur, acknowledge it politely.
        - When you receive a query, determine if the question is about restaurant menu.
        - For queries not related to menu, respond with 'Sorry, I cannot answer this question'.
        - For menu-related queries, first fetch S3 menu data using the get_menu tool.
        - For pricing related queries, use the calculate_order_total tool.
        - Only for menu-related queries that can not be answered from S3 menu data, you can check the menu knowledge base using menu_kb_retrieve tool.
        - If nothing relevant is found using either the get_menu or enu_kb_retrieve tools, ask clarifying questions or refer to contact support.
        """,
    tools=[menu_kb_retrieve, get_menu, calculate_order_total],
)