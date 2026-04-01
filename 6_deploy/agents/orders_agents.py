import os
import json
import uuid
import boto3
import place_order
from datetime import datetime
from strands import Agent, tool
from strands.models import BedrockModel

ORDERS_KNOWLEDGE_BASE_ID = os.environ["ORDERS_KNOWLEDGE_BASE_ID"]
REGION = os.environ["REGION"]
MODEL_ARN = os.environ["MODEL_ARN"]

table = boto3.resource("dynamodb", region_name=REGION).Table("p2p-orders-table")
bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)

@tool(name="orders_kb_retrieve", description="A tool to retrieve data from orders knowledge base")
def orders_kb_retrieve(query: str) -> str:
    """Search the orders knowledge base using retrieve_and_generate."""
    params = {
        "input": {"text": query},
        "retrieveAndGenerateConfiguration": {
          "type": "KNOWLEDGE_BASE",
          "knowledgeBaseConfiguration": {
              "knowledgeBaseId": ORDERS_KNOWLEDGE_BASE_ID,
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

@tool(name="get_recent_order", description="A tool to retrieve data about existing orders")
def get_recent_order(user_id: str) -> dict:
    resp = table.query(
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
        ScanIndexForward=False,
        Limit=1
    )
    if not (items := resp.get("Items", [])):
        return {"message": "No recent order found."}
    o = items[0]
    return {
        "order_id": o.get("order_id", ""),
        "status": o.get("status", ""),
        "items": json.loads(o.get("items", "[]")),
        "total_amount": float(o.get("total_amount", 0))
    }
"""
@tool(name="place_order", description="A tool to place new orders")
def place_order(user_id: str, store_id: str, items: list, total_amount: float) -> dict:
    order_id = str(uuid.uuid4())
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    table.put_item(Item={
        "user_id": user_id,
        "order_timestamp": ts,
        "order_id": order_id,
        "status": "Placed",
        "items": json.dumps(items),
        "store_id": store_id,
        "total_amount": str(total_amount)
    })
    return {"message": f"Order placed successfully with ID: {order_id}"}
"""

orders_agent = Agent(
    model=BedrockModel(model_id=os.environ["MODEL_ID"]),
    system_prompt="""
        - You are 'Orders Assistant', an expert in checking order status, placing new orders and answering questions about orders.
        - Always wrap your answer in <answer> tags.
        - Give 1-2 sentences answers only. Be brief.
        - Only answer using information obtained using available tools. Do not use your own information.
        - If errors occur, acknowledge it politely.
        - When you receive a query, determine if the question is about a restaurant order.
        - For queries not related to orders, respond with 'Sorry, I cannot answer this question'.        
        - For existing order related queries, fetch the order using the get_recent_orders tool. While fetching the order, if any details are needed from the user, ask the user.
        - For new order related queries, use the place_order tool to place new orders.
        - Only if the query can not be answered using the get_recent_orders or place_order tools, you may search the orders knowledge base using orders_kb_retrieve tool.
        - If nothing relevant is found, ask clarifying questions or refer to contact support.
    """,
    tools=[orders_kb_retrieve, get_recent_order, place_order],
)