# payments_agent.py
import os
import json
import boto3
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve, calculator

PAYMENTS_KNOWLEDGE_BASE_ID = os.environ.get("PAYMENTS_KNOWLEDGE_BASE_ID", "")
REGION = os.environ.get("REGION", "us-east-1")
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"  # Use foundation model directly

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)

# === Tools ===
@tool(name="payments_kb_retrieve", description="A tool to retrieve data from payments knowledge base")
def payments_kb_retrieve(query: str) -> str:
    """Search the orders knowledge base using retrieve_and_generate."""
    params = {
        "input": {"text": query},
        "retrieveAndGenerateConfiguration": {
          "type": "KNOWLEDGE_BASE",
          "knowledgeBaseConfiguration": {
              "knowledgeBaseId": PAYMENTS_KNOWLEDGE_BASE_ID,
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

@tool(name="calculate_order_total", description="Calculate total cost based on business pricing rules. Expected input format:items: [{\"type\": \"latte|hot_chocolate|americano|bagel|donut\", \"size\": \"small|medium|large\", \"customizations\": [\"extra_shot\", \"oat_milk\"]}")
def calculate_order_total(items: list) -> dict:
    """
    Calculate total cost with item-specific pricing:
    - Drinks: Varies by type and size + $0.50 per customization
    - Bagels: $4.50 each
    - Donuts: $2.50-$2.75 each
    """
    print(items)
    try:
        # Item category mappings with specific pricing
        drink_items = {
            "latte": {"small": 3.5, "medium": 4.5, "large": 5.5},
            "iced_latte": {"small": 3.5, "medium": 4.5, "large": 5.5},
            "pumpkin_spice_latte": {"small": 4.0, "medium": 5.0, "large": 6.0},
            "hot_chocolate": {"small": 3.0, "medium": 4.0, "large": 5.0},
            "americano": {"small": 2.5, "medium": 3.5, "large": 4.5},
            "coldbrew": {"small": 3.0, "medium": 4.0, "large": 5.0},
            "cold_brew": {"small": 3.0, "medium": 4.0, "large": 5.0},
            "cappuccino": {"small": 3.5, "medium": 4.5, "large": 5.5},
            "mocha": {"small": 4.0, "medium": 5.0, "large": 6.0},
            "espresso": {"small": 2.0, "medium": 2.5, "large": 3.0},
            "macchiato": {"small": 3.5, "medium": 4.5, "large": 5.5},
            "chai": {"small": 3.0, "medium": 4.0, "large": 5.0},
            "tea": {"small": 2.0, "medium": 2.5, "large": 3.0},
            "green_tea": {"small": 2.0, "medium": 2.5, "large": 3.0},
            "black_tea": {"small": 2.0, "medium": 2.5, "large": 3.0}
        }
        
        flat_price_items = {
            "bagel": 4.5,
            "everything_bagel": 4.5,
            "sesame_bagel": 4.5,
            "plain_bagel": 4.0,
            "donut": 2.5,
            "glazed_donut": 2.5,
            "chocolate_donut": 2.75,
            "maple_donut": 2.75,
            "donut_glazed": 2.5,
            "donut_chocolate": 2.75,
            "donut_maple": 2.75
        }
        
        total_cost = 0.0
        
        for item in items:
            item_name = item["type"].lower()
            quantity = item.get("quantity", 1)  # Default to 1 if quantity not specified
            
            # Check if it's a drink item
            if item_name in drink_items:
                size = item["size"].lower()
                base_price = drink_items[item_name].get(size, 4.0)  # Default fallback
                customization_cost = len(item.get("customizations", [])) * 0.5
                item_total = (base_price + customization_cost) * quantity
                total_cost += item_total
                
            # Check if it's a flat-price item
            elif item_name in flat_price_items:
                item_total = flat_price_items[item_name] * quantity
                total_cost += item_total
                
            # Unknown items - return error instead of fallback pricing
            else:
                return {"error": f"Item '{item['type']}' is not available on the menu. Please check with the menu agent for available items."}
        
        # Return the final calculated total, formatted as a currency string
        return {"total_cost": f"${total_cost:.2f}"}
    except Exception as e:
        return {"error": str(e)}

# === Agent ===

payments_agent = Agent(
    model=BedrockModel(model_id='arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0'),
    system_prompt="""
        - You are 'Payments Assistant', an expert in calculating total cost of order and answering any questions on payments policies.
        - Always wrap your answer in <answer> tags.
        - Give 1-2 sentences answers only
        - Only answer using information obtained using available tools. Do not use your own information.
        - If errors occur, acknowledge it politely.
        - When you receive a query, determine if the question is about cost or payment related to a restaurant order.
        - For queries not related to cost or payments, respond with 'Sorry, I cannot answer this question'.          
        - For payments calculation related questions or for finding the total cost, always use the calculate_order_total tool.
        - For transactions, billing, and payment methods related questions, you may use payments_kb_retrieve tool to check the payments knowledge base.
        - If nothing relevant is found in the knowledge base, ask clarifying questions or refer to contact support.
        """,
    tools=[payments_kb_retrieve, calculator, calculate_order_total],
)