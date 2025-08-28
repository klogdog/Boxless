#!/bin/bash

# Google Cloud setup script for Boxless deployment

PROJECT_ID="your-project-id"
REGION="us-central1"
DB_PASSWORD="your-secure-password"

echo "🚀 Setting up Boxless on Google Cloud..."

# Enable required APIs
echo "📡 Enabling Google Cloud APIs..."
gcloud services enable \
    appengine.googleapis.com \
    cloudbuild.googleapis.com \
    cloudtasks.googleapis.com \
    cloudscheduler.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com

# Create Cloud SQL instance
echo "🗃️  Creating Cloud SQL instance..."
gcloud sql instances create boxless-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB

# Create database
gcloud sql databases create boxless_db --instance=boxless-db

# Create database user
gcloud sql users create boxless \
    --instance=boxless-db \
    --password=$DB_PASSWORD

# Create App Engine app
echo "🏗️  Creating App Engine application..."
gcloud app create --region=$REGION

# Create Cloud Tasks queue
echo "📋 Creating Cloud Tasks queue..."
gcloud tasks queues create email-sync-queue --location=$REGION

# Create secrets in Secret Manager
echo "🔐 Creating secrets..."
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-
echo "Please set your Google OAuth credentials:"
read -p "Google Client ID: " GOOGLE_CLIENT_ID
read -p "Google Client Secret: " GOOGLE_CLIENT_SECRET
read -p "Secret Key (32 random characters): " SECRET_KEY

echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets create google-client-id --data-file=-
echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets create google-client-secret --data-file=-
echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=-

# Create Cloud Scheduler job for periodic sync
echo "⏰ Setting up scheduled sync..."
gcloud scheduler jobs create http periodic-email-sync \
    --location=$REGION \
    --schedule="0 */6 * * *" \
    --uri="https://$PROJECT_ID.appspot.com/tasks/sync-all-users" \
    --http-method=POST \
    --headers="Content-Type=application/json"

echo "✅ Google Cloud setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update your OAuth redirect URI to: https://$PROJECT_ID.appspot.com/oauth2/callback"
echo "2. Update app.yaml with your project settings"
echo "3. Run: gcloud app deploy"
echo ""
echo "🔗 Your app will be available at: https://$PROJECT_ID.appspot.com"
