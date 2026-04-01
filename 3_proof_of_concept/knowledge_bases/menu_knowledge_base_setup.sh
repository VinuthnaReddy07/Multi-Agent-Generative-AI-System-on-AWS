#!/bin/bash

set -e

source ~/environment/env.sh

# Create OpenSearch index for menu
echo "Creating OpenSearch index for menu..."
awscurl --service aoss --region $REGION -H "Content-Type: application/json" -X PUT $AOSSENDPOINT/menu_index -d '{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 512
    }
  },
  "mappings": {
    "properties": {
      "documentid": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "engine": "faiss",
          "space_type": "l2"
        }
      },
      "workshop-data": {"type": "text", "index": "true"},
      "workshop-metadata": {"type": "text", "index": "false"}
    }
  }
}'

echo "Waiting 60 seconds for index propagation..."
sleep 60

# Create knowledge base for menu
export MENU_KNOWLEDGE_BASE_ID=$(aws bedrock-agent create-knowledge-base \
  --name menu-knowledge-base \
  --role-arn $ROLE_ARN \
  --knowledge-base-configuration 'type=VECTOR,vectorKnowledgeBaseConfiguration={embeddingModelArn="arn:aws:bedrock:'${REGION}'::foundation-model/amazon.titan-embed-text-v2:0",embeddingModelConfiguration={bedrockEmbeddingModelConfiguration={dimensions=1024}}}' \
  --storage-configuration "type=OPENSEARCH_SERVERLESS,opensearchServerlessConfiguration={collectionArn='${OPENSEARCH_COLLECTION_ARN}',vectorIndexName='menu_index',fieldMapping={vectorField='documentid',textField='workshop-data',metadataField='workshop-metadata'}}" \
  | jq -r '.knowledgeBase.knowledgeBaseId') && \
echo "export MENU_KNOWLEDGE_BASE_ID=$MENU_KNOWLEDGE_BASE_ID" >> ~/environment/env.sh && \
echo "Menu Knowledge Base ID: $MENU_KNOWLEDGE_BASE_ID"

# Create data source for menu
aws bedrock-agent create-data-source \
  --knowledge-base-id $MENU_KNOWLEDGE_BASE_ID \
  --name menu-kb-data-source \
  --data-source-configuration 'type=S3,s3Configuration={bucketArn='"${OPENSEARCH_S3_BUCKET_ARN}"',inclusionPrefixes=["menu_policy/"]}'

export MENU_DATA_SOURCE_ID=$(aws bedrock-agent list-data-sources --knowledge-base-id $MENU_KNOWLEDGE_BASE_ID | jq -r '.dataSourceSummaries[0].dataSourceId') && \
echo "export MENU_DATA_SOURCE_ID=$MENU_DATA_SOURCE_ID" >> ~/environment/env.sh && \
echo "Menu Data Source ID: $MENU_DATA_SOURCE_ID"

# Start ingestion job
ingestion_job_id=$(aws bedrock-agent start-ingestion-job --knowledge-base-id $MENU_KNOWLEDGE_BASE_ID --data-source-id $MENU_DATA_SOURCE_ID | jq -r '.ingestionJob.ingestionJobId')
echo "Ingestion Job ID: $ingestion_job_id"
