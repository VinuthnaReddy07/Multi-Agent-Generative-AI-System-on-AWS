#!/bin/bash

set -euo pipefail

echo "=== Starting Bedrock Knowledge Base Queries ==="

log_query() {
    echo -e "\n\n=============================="
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "=============================="
}

run_query() {
    local prompt="$1"
    local kb_id="$2"
    
    # Use the foundation model ARN directly here
    local model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
    
    echo -e "\nQuestion: $prompt"
    
    echo "Response:"
    aws bedrock-agent-runtime retrieve-and-generate \
        --region us-east-1 \
        --input "{\"text\": \"$prompt\"}" \
        --retrieve-and-generate-configuration "{\"type\": \"KNOWLEDGE_BASE\",\"knowledgeBaseConfiguration\": {\"knowledgeBaseId\": \"$kb_id\",\"modelArn\": \"$model_arn\",\"retrievalConfiguration\": {\"vectorSearchConfiguration\": {\"numberOfResults\": 3}}}}" | jq -r '.output.text'
}

# Remove or comment out this line if it exists
# MODEL_ARN=$MODEL_ARN

log_query "Querying Orders Knowledge Base"
log_query "Using foundation model: arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
run_query "What if my drink arrives cold?" "$ORDERS_KNOWLEDGE_BASE_ID"

log_query "Querying Menu Knowledge Base"
run_query "How much caffeine is in a typical drink?" "$MENU_KNOWLEDGE_BASE_ID"

log_query "Querying Stores Knowledge Base"
run_query "Does stores have public restrooms?" "$STORES_KNOWLEDGE_BASE_ID"

log_query "Querying Payments Knowledge Base"
run_query "What are the different payment methods I can use?" "$PAYMENTS_KNOWLEDGE_BASE_ID"

log_query "Querying Promos Knowledge Base"
run_query "How can I use the promotions?" "$PROMOS_KNOWLEDGE_BASE_ID"

echo -e "\n=== All queries completed ==="
