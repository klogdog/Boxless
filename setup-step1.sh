#!/bin/bash

# Step 1: Basic GCP Setup for inboxzero-468900
echo "🚀 Step 1: Setting up GCP project inboxzero-468900"

PROJECT_ID="inboxzero-468900"
REGION="us-central1"

echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

echo "🔍 Checking if you're authenticated..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ You need to authenticate first. Run:"
    echo "   gcloud auth login"
    exit 1
fi

echo "✅ Authentication check passed"

echo "🔧 Enabling required APIs (this may take a few minutes)..."
gcloud services enable sqladmin.googleapis.com
gcloud services enable appengine.googleapis.com
gcloud services enable cloudtasks.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

echo "✅ Step 1 complete!"
echo ""
echo "🔒 IMPORTANT: We'll use Google Secret Manager for all sensitive data"
echo "   - No secrets will be committed to git"
echo "   - All credentials stored securely in GCP"
echo ""
echo "🎯 Next: I'll give you Step 2 to set up Secret Manager"
