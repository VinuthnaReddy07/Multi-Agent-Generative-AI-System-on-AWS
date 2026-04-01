#!/bin/bash

# Script to check if required environment variables are set

echo "=== Lab Environment Variables Check ==="
echo

# Check required environment variables
required_vars=(
    "AWS_REGION"
    "STACK_NAME" 
    "DB_CLUSTER_NAME"
    "DB_SECRET_NAME"
    "WORKSHOP_S3_BUCKET"
)

all_set=true

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ $var: NOT SET"
        all_set=false
    else
        echo "✅ $var: ${!var}"
    fi
done

echo
if [ "$all_set" = true ]; then
    echo "🎉 All required environment variables are set!"
else
    echo "⚠️  Some environment variables are missing."
    echo "   These should be automatically set by the lab environment."
    echo "   If you're seeing this error, there may be an issue with the lab setup."
fi

echo
echo "=== AWS Resource Verification ==="

# Test AWS connectivity
if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "✅ AWS CLI: Connected"
else
    echo "❌ AWS CLI: Not connected or configured"
    exit 1
fi

# Check if DB cluster exists (if DB_CLUSTER_NAME is set)
if [ -n "$DB_CLUSTER_NAME" ]; then
    if aws rds describe-db-clusters --db-cluster-identifier "$DB_CLUSTER_NAME" >/dev/null 2>&1; then
        echo "✅ DB Cluster: $DB_CLUSTER_NAME exists"
    else
        echo "❌ DB Cluster: $DB_CLUSTER_NAME not found"
    fi
fi

# Check if secret exists (if DB_SECRET_NAME is set)
if [ -n "$DB_SECRET_NAME" ]; then
    if aws secretsmanager describe-secret --secret-id "$DB_SECRET_NAME" >/dev/null 2>&1; then
        echo "✅ Secret: $DB_SECRET_NAME exists"
    else
        echo "❌ Secret: $DB_SECRET_NAME not found"
    fi
fi

echo
echo "=== Environment Check Complete ==="