#!/bin/bash

# Script to discover and set up environment variables for the lab
# This script uses AWS service APIs to discover resources instead of CloudFormation outputs

echo "=== Setting up Lab Environment Variables ==="
echo

# Create environment file if it doesn't exist
mkdir -p ~/environment
ENV_FILE=~/environment/env.sh

# Clear the environment file to avoid duplicates
> $ENV_FILE

# Basic AWS environment
export REGION=$(aws configure get region)
echo "export REGION=$REGION" >> $ENV_FILE
echo "Region: $REGION"

export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "export ACCOUNT_ID=$ACCOUNT_ID" >> $ENV_FILE
echo "Account ID: $ACCOUNT_ID"

# Model configuration
export MODEL_ID="us.amazon.nova-pro-v1:0"
echo "export MODEL_ID=$MODEL_ID" >> $ENV_FILE
echo "Model ID: $MODEL_ID"

export MODEL_ARN="arn:aws:bedrock:${REGION}:${ACCOUNT_ID}:inference-profile/${MODEL_ID}"
echo "export MODEL_ARN=$MODEL_ARN" >> $ENV_FILE
echo "Model ARN: $MODEL_ARN"

echo
echo "=== Discovering AWS Resources ==="

# Discover Aurora DB cluster by name pattern
echo "Looking for Aurora DB cluster..."
DB_CLUSTER_NAME=$(aws rds describe-db-clusters --query 'DBClusters[?starts_with(DBClusterIdentifier, `tot-aurora-cluster`)].DBClusterIdentifier' --output text | head -1)
if [ -n "$DB_CLUSTER_NAME" ]; then
    echo "export DB_CLUSTER_NAME=$DB_CLUSTER_NAME" >> $ENV_FILE
    echo "✅ Found DB Cluster: $DB_CLUSTER_NAME"
else
    echo "❌ Aurora DB cluster not found"
fi

# Discover Secrets Manager secret
echo "Looking for database credentials secret..."
DB_SECRET_NAME=$(aws secretsmanager list-secrets --query 'SecretList[?starts_with(Name, `tot-aurora-db-credentials`)].Name' --output text | head -1)
if [ -n "$DB_SECRET_NAME" ]; then
    echo "export DB_SECRET_NAME=$DB_SECRET_NAME" >> $ENV_FILE
    echo "✅ Found DB Secret: $DB_SECRET_NAME"
else
    echo "❌ Database credentials secret not found"
fi

# Discover DynamoDB tables
echo "Looking for DynamoDB tables..."
ORDERS_TABLE=$(aws dynamodb list-tables --query 'TableNames[?starts_with(@, `tot-orders-table`)]' --output text | head -1)
if [ -n "$ORDERS_TABLE" ]; then
    echo "export ORDERS_TABLE=$ORDERS_TABLE" >> $ENV_FILE
    echo "✅ Found Orders Table: $ORDERS_TABLE"
else
    echo "❌ Orders table not found"
fi

SESSIONS_TABLE=$(aws dynamodb list-tables --query 'TableNames[?starts_with(@, `tot-sessions-table`)]' --output text | head -1)
if [ -n "$SESSIONS_TABLE" ]; then
    echo "export SESSIONS_TABLE=$SESSIONS_TABLE" >> $ENV_FILE
    echo "✅ Found Sessions Table: $SESSIONS_TABLE"
else
    echo "❌ Sessions table not found"
fi

# Discover OpenSearch collection
echo "Looking for OpenSearch collection..."
OPENSEARCH_COLLECTION=$(aws opensearchserverless list-collections --query 'collectionSummaries[?starts_with(name, `tot-`) || contains(name, `workshop`) || contains(name, `opensearch`) || contains(name, `lab`)].name' --output text | head -1)
if [ -n "$OPENSEARCH_COLLECTION" ]; then
    # Get collection endpoint
    AOSSENDPOINT=$(aws opensearchserverless batch-get-collection --names "$OPENSEARCH_COLLECTION" --query 'collectionDetails[0].collectionEndpoint' --output text)
    echo "export OPENSEARCH_COLLECTION=$OPENSEARCH_COLLECTION" >> $ENV_FILE
    echo "export AOSSENDPOINT=$AOSSENDPOINT" >> $ENV_FILE
    echo "✅ Found OpenSearch Collection: $OPENSEARCH_COLLECTION"
    echo "✅ OpenSearch Endpoint: $AOSSENDPOINT"
    
    # Get collection ARN
    OPENSEARCH_COLLECTION_ARN=$(aws opensearchserverless batch-get-collection --names "$OPENSEARCH_COLLECTION" --query 'collectionDetails[0].arn' --output text)
    echo "export OPENSEARCH_COLLECTION_ARN=$OPENSEARCH_COLLECTION_ARN" >> $ENV_FILE
    echo "✅ OpenSearch Collection ARN: $OPENSEARCH_COLLECTION_ARN"
else
    echo "❌ OpenSearch collection not found"
fi

# Discover S3 buckets
echo "Looking for workshop S3 bucket..."
WORKSHOP_S3_BUCKET=$(aws s3api list-buckets --query 'Buckets[?starts_with(Name, `tot-input-docs-bucket-`)].Name' --output text | head -1)
if [ -n "$WORKSHOP_S3_BUCKET" ]; then
    echo "export WORKSHOP_S3_BUCKET=$WORKSHOP_S3_BUCKET" >> $ENV_FILE
    echo "✅ Found Workshop S3 Bucket: $WORKSHOP_S3_BUCKET"
    
    # Get the bucket ARN for OpenSearch knowledge base data sources
    OPENSEARCH_S3_BUCKET_ARN="arn:aws:s3:::$WORKSHOP_S3_BUCKET"
    echo "export OPENSEARCH_S3_BUCKET_ARN=$OPENSEARCH_S3_BUCKET_ARN" >> $ENV_FILE
    echo "✅ OpenSearch S3 Bucket ARN: $OPENSEARCH_S3_BUCKET_ARN"
    
    # Also set the bucket name for compatibility
    echo "export OpenSearch_BUCKET_NAME=$WORKSHOP_S3_BUCKET" >> $ENV_FILE
else
    echo "❌ Workshop S3 bucket not found"
fi

# Discover IAM role for Bedrock
echo "Looking for Bedrock execution role..."
ROLE_ARN=$(aws iam list-roles --query 'Roles[?starts_with(RoleName, `AmazonBedrockExecutionRoleForKnowledgeBase`)].Arn' --output text | head -1)
if [ -n "$ROLE_ARN" ]; then
    echo "export ROLE_ARN=$ROLE_ARN" >> $ENV_FILE
    echo "✅ Found Bedrock Role: $ROLE_ARN"
else
    echo "❌ Bedrock execution role not found"
fi

echo
echo "=== Loading Environment Variables ==="
source $ENV_FILE
echo "✅ Environment variables loaded from $ENV_FILE"



echo
echo "=== Environment Setup Complete ==="
echo "Run 'source ~/environment/env.sh' to load these variables in new terminal sessions"