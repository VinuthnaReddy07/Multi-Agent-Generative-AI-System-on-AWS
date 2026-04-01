import os
import json
import pymysql
import boto3
import codecs
import traceback
from strands import Agent, tool
from strands.models import BedrockModel

STORES_KNOWLEDGE_BASE_ID = os.environ.get("STORES_KNOWLEDGE_BASE_ID", "")
REGION = os.environ.get("REGION", "us-east-1")
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"  # Use foundation model directly

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)

print("Fetching Aurora endpoint...")
rds = boto3.client('rds')
clusters = rds.describe_db_clusters()
host = next(
    c['Endpoint'] for c in clusters['DBClusters']
    if c['DBClusterIdentifier'].startswith('tot-aurora-cluster')
)
print(f"Aurora endpoint resolved: {host}")

print("Fetching DB credentials from Secrets Manager...")
secrets_client = boto3.client('secretsmanager')
secret_value = secrets_client.get_secret_value(SecretId='tot-aurora-db-credentials')
raw = secret_value['SecretString']
clean = codecs.decode(raw, 'unicode_escape')
credentials = json.loads(clean)

db_user = credentials['username']
db_pass = credentials['password']
print(f"DB user: {db_user}")

def get_conn():
    try:
        conn = pymysql.connect(
            host=host,
            user=db_user,
            password=db_pass,
            database="StoresDB",
            connect_timeout=5
        )
        print("Successfully connected to the database.")
        return conn
    except Exception as e:
        print("Failed to connect to DB:")
        traceback.print_exc()
        raise

def serialize_row(row, columns):
    from datetime import timedelta
    def serialize(value):
        return str(value) if isinstance(value, timedelta) else value
    return dict(zip(columns, [serialize(v) for v in row]))

@tool(name="stores_kb_retrieve", description="A tool to retrieve data from the stores knowledge base")
def stores_kb_retrieve(query: str) -> str:
    print(f"Running stores_kb_retrieve with query: {query}")
    params = {
        "input": {"text": query},
        "retrieveAndGenerateConfiguration": {
          "type": "KNOWLEDGE_BASE",
          "knowledgeBaseConfiguration": {
              "knowledgeBaseId": STORES_KNOWLEDGE_BASE_ID,
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
        print("stores_kb_retrieve response received.")
        return response.get("output", {}).get("text", "No relevant information found in the knowledge base.")
    except Exception as e:
        print("Failed in stores_kb_retrieve:")
        traceback.print_exc()
        return f"Failed to retrieve information: {str(e)}"

@tool(name="list_stores", description="A tool to retrieve the list of stores")
def list_stores(query: str = "") -> list:
    print("Running list_stores...")
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT store_id, name, address, city, state, zip_code,
                       latitude, longitude, has_drive_thru, hours_start, hours_end
                FROM stores
            """)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            print(f"Fetched {len(rows)} stores.")
            return [serialize_row(row, columns) for row in rows]
    except Exception as e:
        print("Error in list_stores:")
        traceback.print_exc()
        return [{"error": str(e)}]

@tool(name="get_store_by_id", description="A tool to find a store by its ID")
def get_store_by_id(store_id: str) -> dict:
    print(f"Running get_store_by_id with store_id: {store_id}")
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT store_id, name, address, city, state, zip_code,
                       latitude, longitude, has_drive_thru, hours_start, hours_end
                FROM stores WHERE store_id = %s
            """, (store_id,))
            row = cursor.fetchone()
            if not row:
                print("Store not found.")
                return {"message": "Store not found"}
            columns = [col[0] for col in cursor.description]
            return serialize_row(row, columns)
    except Exception as e:
        print("Error in get_store_by_id:")
        traceback.print_exc()
        return {"error": str(e)}

@tool(name="search_store_by_name", description="A tool to find a store by its name")
def search_store_by_name(name: str) -> list:
    print(f"Running search_store_by_name with name like: %{name}%")
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT store_id, name, address, city, state, zip_code,
                       latitude, longitude, has_drive_thru, hours_start, hours_end
                FROM stores WHERE name LIKE %s
            """, (f"%{name}%",))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            print(f"Found {len(rows)} matching stores.")
            return [serialize_row(row, columns) for row in rows]
    except Exception as e:
        print("Error in search_store_by_name:")
        traceback.print_exc()
        return [{"error": str(e)}]

stores_agent = Agent(
    model=BedrockModel(model_id='arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0'),
    system_prompt="""
        - You are 'Stores Assistant', an expert in searching for restaurant stores and answering store policy related questions.
        - Always wrap your answer in <answer> tags.
        - Give 1-2 sentence answers only. Be brief.
        - Only answer using information obtained using available tools. Do not use your own information.
        - If errors occur, acknowledge it politely.
        - When you receive a query, determine if the question is about stores or restaurants.
        - For queries not related to stores or restaurants, respond with 'Sorry, I cannot answer this question'.   
        - If answering the query requires stores or restaurants related data, first use the following tools: list_stores, get_store_by_id, or search_store_by_name.
        - Only if necessary and only after trying all other tools, you may use the stores_kb_retrieve tool check the stores knowledge base.
        - If nothing relevant is found in the knowledge base, ask clarifying questions or refer to contact support.
    """,
    tools=[stores_kb_retrieve, list_stores, get_store_by_id, search_store_by_name],
)

print("Stores agent setup complete.")
