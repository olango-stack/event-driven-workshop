#!/bin/bash

# Deploy Async Frontend Script for CNS203 Workshop
# This script replaces the sync frontend with the async version

set -e  # Exit on any error

echo "🚀 Deploying Enhanced Async Frontend..."

# The bucket name output is missing from the deployed stack
# Use a simple approach: find the bucket by name pattern
echo "📦 Getting S3 bucket name..."
BUCKET_NAME=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'cns203cdkbackendstack-cns203frontendbucket')].Name" --output text)

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Error: Could not find CNS203 frontend bucket"
    echo "Available buckets:"
    aws s3api list-buckets --query "Buckets[].Name" --output text
    exit 1
fi

# Get the frontend URL
FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name CNS203CdkBackendStack \
    --query "Stacks[0].Outputs[?OutputKey=='CNS203FrontendUrl'].OutputValue" \
    --output text)

echo "📦 Frontend bucket: $BUCKET_NAME"
echo "🌐 Frontend URL: $FRONTEND_URL"

# Clear the bucket completely to avoid file conflicts
echo "🧹 Clearing existing frontend files..."
aws s3 rm s3://$BUCKET_NAME/ --recursive --quiet

# Upload the async frontend
echo "⬆️  Uploading async frontend files..."
aws s3 sync ../react-frontend-async/build/ s3://$BUCKET_NAME/ --quiet

echo "✅ Frontend has been successfully updated!"
echo "🌐 Frontend URL: $FRONTEND_URL"