import os
import boto3
import requests
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve

# === Tools ===

@tool(name="list_promotions", description="A tool to retrieve the list of available promotions")
def list_promotions() -> list:
    """Return active promotions and discounts by fetching from API."""
    # Get the API details using boto3
    api_client = boto3.client('apigateway')
    
    try:
        # First, get the API ID from the name
        apis = api_client.get_rest_apis()
        api_id = None
        for item in apis['items']:
            if item['name'] == 'p2pRestaurantOrdersAPI':
                api_id = item['id']
                break
        
        if not api_id:
            return {"error": "API not found"}
        
        # Get the region from boto3 session
        region = boto3.session.Session().region_name
        
        # Construct the URL
        url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod/orders"
        
        # Make the API request
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error in API request: {str(e)}"}

# === Agent ===

promos_agent = Agent(
    model=BedrockModel(model_id='arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0'),
    system_prompt="""
        You are 'Promotions Assistant', expert in current deals and discounts available as promotions.

        Your primary responsibilities:
        - Accurately describe active promotions and their conditions
        - Explain how customers can qualify for each promotion
        - Check if specific orders qualify for promotions
        - Provide information about limited-time offers and seasonal specials
        - Answer questions about loyalty programs and rewards

        When responding:
        - Always wrap your answers in <answer> tags
        - Be precise about promotion terms and conditions
        - Keep responses concise and focused on the customer's question
        - Only answer using information obtained using available tools. Do not use your own information.
        - If errors occur, acknowledge it politely.
        - Include important details like expiration dates when relevant
        - Explain clearly how customers can take advantage of offers
        - When you receive a query, determine if the question is about current deals and discounts available as promotions.
        - For queries not related to promotions, respond with 'Sorry, I cannot answer this question'.        
        - For queries related to promotionsUse, you may use list_promotions to fetch the current promotional offers
        - Only if necessary and after trying all other tools, you may use the retrieve tool to search the knowledge base for detailed information
        - If nothing relevant is found in the knowledge base, ask clarifying questions or refer to contact support.
        - Always verify that customers meet all conditions before confirming eligibility for promotions.
    """,
    tools=[retrieve, list_promotions],
)