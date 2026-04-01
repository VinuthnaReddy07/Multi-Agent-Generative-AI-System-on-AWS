import os
import sys
import json
from strands import Agent, tool
from strands.models import BedrockModel
import logging
from bedrock_agentcore.runtime import BedrockAgentCoreApp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orders_agents, menu_agents, payments_policy_agents, stores_agents, promos_agents

# AgentCore app instance (assumes BedrockAgentCoreApp is available in your env)
app = BedrockAgentCoreApp()

# Strands logger
strands_logger = logging.getLogger("strands")
strands_logger.setLevel(logging.DEBUG)

# === Tool Wrappers ===
@tool(name="orders_agent_tool", description="A tool for checking order status, placing new orders and answering questions about orders.")
def orders_agent_tool(query: str) -> str:
    response = orders_agents.orders_agent(query)
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    return str(response)

@tool(name="menu_agent_tool", description="A tool to answer questions about restaurant menus")
def menu_agent_tool(query: str) -> str:
    response = menu_agents.menu_agent(query)
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    return str(response)

@tool(name="payments_policy_agent_tool", description="An AI assistant trained to answer customer questions about the cafe's payment policies. It uses an internal knowledge base to provide information on accepted payment types, transaction processes, refunds, and troubleshooting.")
def payments_policy_agent_tool(query: str) -> str:
    response = payments_policy_agent.payments_policy_agent(query)
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    return str(response)

@tool(name="stores_agent_tool", description="A tool to answer questions about restaurant stores and store policies.")
def stores_agent_tool(query: str) -> str:
    response = stores_agents.stores_agent(query)
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    return str(response)

@tool(name="promos_agent_tool", description="A tool to answer questions about current deals and discounts available as promotions")
def promos_agent_tool(query: str) -> str:
    response = promos_agents.promos_agent(query)
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    return str(response)

# === Orchestrator ===
orchestrator_prompt = """
You are the Orchestrator Assistant who helps users place drink and food orders at restaurants. 
You can also answer queries about restaurant stores, menu items, prices, promotions and prior orders.

You respond to quries following these routing guidelines:
- Respond directly to general inquiries that do not require use of tools or specialized knowledge
- For domain-specific (menu, stores, orders, payments or promotions) queries, use the most appropriate tool (specialized agent)
- If a query spans multiple domains, prioritize using the most relevant tool first, and use additional tools after that only if required

Direct user queries to the appropriate tool (specialized agent):
- For order-related queries (order status, history, modifications): use the orders_agent_tool
- For menu-related queries (item availability, ingredients, allergens): use the menu_agent_tool
- For payment-related queries (pricing, cost calculation, payment methods): use the payments_agent_tool
- For store-related queries (locations, hours, amenities, drive-thru availability): use the stores_agent_tool
- For promotion-related queries (deals, discounts, special offers, loyalty programs): use the promos_agent_tool

When a new order request is received:
- Only if you have not checked already, use the menu_agent_tool to confirm that all requested items exist on the menu. If any item is invalid, suggest valid alternatives from the menu.
- For drink orders, always ask the user to confirm the drink size and any customizations before proceeding.
- Then Use the payments_agent_tool to calculate the total cost of the order.
- CRITICAL: You MUST immediately inform the customer about the exact items being ordered and the total cost. Display this information clearly before asking for any personal information.
- After showing the total cost, ask for the customer's name or rewards member ID to complete the order.
- If store ID is missing, use random number as default store ID.
- If user ID is missing, use random number for user ID.
- Finally, use the orders_agent_tool to place the order, and provide the user with the order ID.
- CRITICAL: When displaying the final order confirmation, you MUST include both the Order ID AND the total cost. Always say something like: 'Your order [Order ID] for $[total cost] is confirmed. Please listen for your name to be called.'

Your responses should:
- Be direct and to the point
- Not mention the source of information (like document IDs or scores)
- Not include any metadata or technical details
- Be conversational but brief, respond with only 1-2 sentences if possible.
- For domain-specific topics, only answer using information obtained using available tools. Do not use your own information.
- Acknowledge when information is conflicting or missing
- Begin all responses with 

- Never apologize for using a tool or mention that you are routing to a specialized agent
- Present store locations and hours clearly and accurately when requested
- Format promotional offers in a way that highlights savings and conditions
- If store ID is missing, use random number as default store ID.
- If user ID is missing, use random number for user ID.
"""

gr_id  = os.getenv("GUARDRAIL_ID")
gr_ver = os.getenv("GUARDRAIL_VERSION")
gr_trc = os.getenv("GUARDRAIL_TRACE")

opt = {}
if gr_id and gr_ver:
    opt["guardrail_id"] = gr_id
    opt["guardrail_version"] = gr_ver
    if gr_trc:
        opt["guardrail_trace"] = gr_trc

orchestrator = Agent(
    model=BedrockModel(model_id=os.environ["MODEL_ID"], **opt),
    system_prompt=orchestrator_prompt,
    tools=[orders_agent_tool, menu_agent_tool, payments_policy_agent_tool, stores_agent_tool, promos_agent_tool],
)

# === AgentCore entrypoint ===
@app.entrypoint
def strands_agent_bedrock(payload, context):
    # Pass only the prompt; no prior-message logic
    user_input = payload.get("prompt")

    os.environ["BYPASS_TOOL_CONSENT"] = "true"

    # Log the context session_id (for tracing only)
    print(f"Session ID: {context.session_id}")

    # Invoke orchestrator with just the prompt
    response = orchestrator(user_input)

    # Prefer a text attribute if present; else stringify
    assistant_text = getattr(response, "text", None) or str(response)

    # Log single-line response
    print(assistant_text)

    return assistant_text or " "

if __name__ == "__main__":
    app.run()
