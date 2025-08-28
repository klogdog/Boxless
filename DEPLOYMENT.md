# 🚀 Boxless - Google Cloud Platform Deployment Guide

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Google Cloud Configuration](#google-cloud-configuration)
- [Application Configuration](#application-configuration)
- [Deployment Process](#deployment-process)
- [Post-Deployment Setup](#post-deployment-setup)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

## Overview

Boxless is a production-ready Gmail API integration platform designed for Google Cloud Platform. It provides automated email synchronization with background processing capabilities, eliminating the need for users to keep the frontend open for email syncing.

### Key Features
- **🔐 OAuth 2.0 Integration** with Gmail API
- **📧 Automated Email Sync** with background processing
- **🗄️ PostgreSQL Database** on Cloud SQL
- **⚡ Scalable Architecture** with App Engine
- **📊 Real-time Monitoring** and status tracking
- **🔄 Scheduled Tasks** for continuous synchronization

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vue.js SPA    │◄──►│  FastAPI Backend │◄──►│  PostgreSQL DB  │
│  (Frontend)     │    │   (App Engine)   │    │  (Cloud SQL)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        │                        ▼                        │
        │              ┌──────────────────┐               │
        │              │  Cloud Tasks     │               │
        │              │  (Background)    │               │
        │              └──────────────────┘               │
        │                        │                        │
        │                        ▼                        │
        │              ┌──────────────────┐               │
        └──────────────┤ Cloud Scheduler  │───────────────┘
                       │ (Periodic Sync)  │
                       └──────────────────┘
```

### Components
- **App Engine**: Hosts FastAPI backend and serves Vue.js frontend
- **Cloud SQL**: PostgreSQL database for email storage
- **Cloud Tasks**: Background job processing for email sync
- **Cloud Scheduler**: Automated periodic synchronization
- **Secret Manager**: Secure storage of API keys and secrets
- **Cloud Build**: CI/CD pipeline for automated deployment

## Prerequisites

### Required Accounts & Access
1. **Google Cloud Platform Account** with billing enabled
2. **Gmail Account** for API testing
3. **Google Cloud Project** with Owner or Editor permissions

### Required Software
- **Google Cloud SDK** (gcloud CLI) - [Install Guide](https://cloud.google.com/sdk/docs/install)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.11+** - [Download](https://python.org/)
- **Git** - [Download](https://git-scm.com/)

### Verify Prerequisites
```bash
# Check gcloud installation
gcloud version

# Check Node.js version
node --version  # Should be 18+

# Check Python version
python3 --version  # Should be 3.11+

# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login
```

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/klogdog/Boxless.git
cd Boxless
```

### 2. Create Google Cloud Project
```bash
# Set project variables
export PROJECT_ID="boxless-$(date +%s)"  # Unique project ID
export REGION="us-central1"

# Create new project
gcloud projects create $PROJECT_ID --name="Boxless Production"

# Set as default project
gcloud config set project $PROJECT_ID

# Link billing account (replace with your billing account ID)
gcloud billing projects link $PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 3. Enable Required APIs
```bash
# Enable all required Google Cloud APIs
gcloud services enable \
    appengine.googleapis.com \
    cloudbuild.googleapis.com \
    cloudtasks.googleapis.com \
    cloudscheduler.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudresourcemanager.googleapis.com \
    gmail.googleapis.com
```

## Google Cloud Configuration

### 1. Create App Engine Application
```bash
# Create App Engine app in specified region
gcloud app create --region=$REGION
```

### 2. Set Up Cloud SQL Database

#### Create PostgreSQL Instance
```bash
# Generate secure password
export DB_PASSWORD=$(openssl rand -base64 32)

# Create Cloud SQL instance
gcloud sql instances create boxless-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --maintenance-release-channel=production

# Set root password
gcloud sql users set-password postgres \
    --instance=boxless-db \
    --password=$DB_PASSWORD

# Create application database
gcloud sql databases create boxless_db --instance=boxless-db

# Create application user
gcloud sql users create boxless \
    --instance=boxless-db \
    --password=$DB_PASSWORD
```

#### Configure Database Security
```bash
# Add your IP for local testing (optional)
MY_IP=$(curl -s https://api.ipify.org)
gcloud sql instances patch boxless-db \
    --authorized-networks=$MY_IP/32

# Enable Cloud SQL proxy for App Engine
gcloud sql instances patch boxless-db \
    --enable-proxy
```

### 3. Set Up Cloud Tasks
```bash
# Create task queue for background email sync
gcloud tasks queues create email-sync-queue \
    --location=$REGION \
    --max-concurrent-dispatches=5 \
    --max-dispatches-per-second=2
```

### 4. Configure Secret Manager
```bash
# Store database password
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-

# You'll add OAuth secrets after configuring Gmail API
```

### 5. Gmail API Configuration

#### Enable Gmail API
```bash
# Gmail API should already be enabled from previous step
gcloud services list --enabled | grep gmail
```

#### Create OAuth 2.0 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Click **+ CREATE CREDENTIALS > OAuth 2.0 Client IDs**
4. Configure OAuth consent screen:
   - **Application type**: Web application
   - **Name**: Boxless Production
   - **Authorized JavaScript origins**: `https://$PROJECT_ID.appspot.com`
   - **Authorized redirect URIs**: `https://$PROJECT_ID.appspot.com/oauth2/callback`
5. Download credentials JSON file

#### Store OAuth Credentials
```bash
# Store OAuth credentials in Secret Manager
# Replace with your actual values from the downloaded JSON
export GOOGLE_CLIENT_ID="your-client-id.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"

echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets create google-client-id --data-file=-
echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets create google-client-secret --data-file=-

# Generate secure secret key for application
export SECRET_KEY=$(openssl rand -hex 32)
echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=-
```

### 6. Set Up Cloud Scheduler
```bash
# Create periodic sync job (runs every 6 hours)
gcloud scheduler jobs create http periodic-email-sync \
    --location=$REGION \
    --schedule="0 */6 * * *" \
    --uri="https://$PROJECT_ID.appspot.com/tasks/sync-all-users" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --time-zone="UTC"
```

## Application Configuration

### 1. Update App Engine Configuration
Create or update `app.yaml` with your project details:

```yaml
# app.yaml
runtime: python311

env_variables:
  # Database Configuration
  DATABASE_URL: postgresql://boxless:$$DB_PASSWORD@/boxless_db?host=/cloudsql/$$PROJECT_ID:$$REGION:boxless-db
  ASYNC_DATABASE_URL: postgresql+asyncpg://boxless:$$DB_PASSWORD@/boxless_db?host=/cloudsql/$$PROJECT_ID:$$REGION:boxless-db
  
  # Gmail API Configuration  
  GOOGLE_CLIENT_ID: $$GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET: $$GOOGLE_CLIENT_SECRET
  GOOGLE_REDIRECT_URI: https://$$PROJECT_ID.appspot.com/oauth2/callback
  
  # Application Configuration
  BACKEND_URL: https://$$PROJECT_ID.appspot.com
  FRONTEND_URL: https://$$PROJECT_ID.appspot.com
  SECRET_KEY: $$SECRET_KEY
  ENVIRONMENT: production
  
  # Background Jobs Configuration
  ENABLE_BACKGROUND_SYNC: true
  SYNC_INTERVAL_MINUTES: 30
  GOOGLE_CLOUD_PROJECT: $$PROJECT_ID
  GOOGLE_CLOUD_REGION: $$REGION

# Static files for frontend
handlers:
- url: /static/.*
  static_dir: apps/frontend/dist
  secure: always

- url: /.*
  script: auto
  secure: always

# Instance configuration
instance_class: F2
automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

# Cloud SQL connection
beta_settings:
  cloud_sql_instances: $$PROJECT_ID:$$REGION:boxless-db

# Health check configuration
readiness_check:
  path: "/health"
  check_interval_sec: 5
  timeout_sec: 4
  failure_threshold: 2
  success_threshold: 2

liveness_check:
  path: "/health"
  check_interval_sec: 30
  timeout_sec: 4
  failure_threshold: 4
  success_threshold: 2
```

### 2. Configure Environment-Specific Settings

#### Production Environment Variables
```bash
# Set production environment variables
gcloud app deploy --set-env-vars="
ENVIRONMENT=production,
ENABLE_BACKGROUND_SYNC=true,
SYNC_INTERVAL_MINUTES=30,
GOOGLE_CLOUD_PROJECT=$PROJECT_ID,
GOOGLE_CLOUD_REGION=$REGION
"
```

#### Database Connection Configuration
The application will automatically use Cloud SQL Proxy in production. Ensure your `database.py` includes:

```python
# Production database configuration
if os.getenv('ENVIRONMENT') == 'production':
    DATABASE_URL = os.getenv('DATABASE_URL')
    ASYNC_DATABASE_URL = os.getenv('ASYNC_DATABASE_URL')
else:
    # Development configuration
    DATABASE_URL = "sqlite:///./boxless.db"
    ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./boxless.db"
```

### 3. Update Frontend Configuration

#### Production API Base URL
Update `apps/frontend/src/components/GmailAuth.vue`:

```javascript
// API base URL detection
const API_BASE = import.meta.env.PROD 
  ? window.location.origin  // Production: same origin
  : window.location.hostname === 'localhost' 
    ? 'http://localhost:8000'  // Development: local backend
    : 'http://127.0.0.1:8000'   // Development: alternative
```

#### Build Configuration
Update `apps/frontend/vite.config.ts` for production builds:

```typescript
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'static',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'axios']
        }
      }
    }
  },
  define: {
    __VUE_PROD_DEVTOOLS__: false
  }
})
```

## Deployment Process

### 1. Prepare Application Files

#### Install Dependencies
```bash
# Install Python dependencies
cd apps/backend
pip install -r requirements.txt

# Install Node.js dependencies
cd ../frontend
npm install
```

#### Build Frontend
```bash
# Build production frontend
cd apps/frontend
npm run build

# Verify build output
ls -la dist/
```

### 2. Configure Cloud Build (Optional)

Create `cloudbuild.yaml` for automated deployments:

```yaml
# cloudbuild.yaml
steps:
  # Build Frontend
  - name: 'node:18'
    entrypoint: 'npm'
    args: ['ci']
    dir: 'apps/frontend'
    
  - name: 'node:18'
    entrypoint: 'npm'
    args: ['run', 'build']
    dir: 'apps/frontend'
    
  # Install Python dependencies
  - name: 'python:3.11'
    entrypoint: 'pip'
    args: ['install', '-r', 'requirements.txt', '--target', 'lib']
    dir: 'apps/backend'
    
  # Run database migrations
  - name: 'python:3.11'
    entrypoint: 'python'
    args: ['migrate.py']
    dir: 'apps/backend'
    env:
      - 'DATABASE_URL=postgresql://boxless:$$_DB_PASSWORD@/boxless_db?host=/cloudsql/$$PROJECT_ID:$$_REGION:boxless-db'
    secretEnv: ['_DB_PASSWORD']
    
  # Deploy to App Engine
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args: ['app', 'deploy', '--quiet']

# Secret configuration
availableSecrets:
  secretManager:
  - versionName: projects/$$PROJECT_ID/secrets/db-password/versions/latest
    env: '_DB_PASSWORD'

# Build configuration
substitutions:
  _REGION: 'us-central1'

timeout: 1200s
```

### 3. Deploy Application

#### Manual Deployment
```bash
# Return to project root
cd /path/to/Boxless

# Deploy to App Engine
gcloud app deploy --quiet

# Deploy with specific version (optional)
gcloud app deploy --version=v1 --no-promote --quiet
```

#### Automated Deployment with Cloud Build
```bash
# Submit build to Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# Set up automated triggers (optional)
gcloud builds triggers create github \
    --repo-name=Boxless \
    --repo-owner=klogdog \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

### 4. Database Migration
```bash
# Run database migrations after deployment
gcloud app deploy --version=migration \
    apps/backend/migrate.py \
    --no-promote --quiet

# Promote migration version temporarily
gcloud app versions migrate migration --service=default

# Run migration
curl https://$PROJECT_ID.appspot.com/migrate

# Switch back to main version
gcloud app versions migrate v1 --service=default
```

## Post-Deployment Setup

### 1. Verify Deployment
```bash
# Check application status
gcloud app browse

# Verify services
gcloud app services list

# Check versions
gcloud app versions list
```

### 2. Test Application Endpoints
```bash
# Test health endpoint
curl https://$PROJECT_ID.appspot.com/health

# Test API documentation
curl https://$PROJECT_ID.appspot.com/docs

# Test OAuth URL generation
curl https://$PROJECT_ID.appspot.com/gmail/auth-url
```

### 3. Configure OAuth Redirect
1. Update OAuth redirect URI in Google Cloud Console
2. Add: `https://$PROJECT_ID.appspot.com/oauth2/callback`
3. Test OAuth flow through web interface

### 4. Verify Background Tasks
```bash
# Check task queue
gcloud tasks queues describe email-sync-queue --location=$REGION

# Test background sync endpoint
curl -X POST https://$PROJECT_ID.appspot.com/gmail/sync-background

# Check scheduler job
gcloud scheduler jobs describe periodic-email-sync --location=$REGION
```

### 5. Set Up Monitoring

#### Enable Application Insights
```bash
# Create custom metrics
gcloud logging metrics create email_sync_success \
    --description="Successful email synchronizations" \
    --log-filter='resource.type="gae_app" AND textPayload:"Sync completed successfully"'

gcloud logging metrics create email_sync_errors \
    --description="Failed email synchronizations" \
    --log-filter='resource.type="gae_app" AND textPayload:"Sync failed"'
```

#### Set Up Alerting
```bash
# Create notification channel (replace with your email)
gcloud alpha monitoring channels create \
    --display-name="Email Alerts" \
    --type=email \
    --channel-labels=email_address=your-email@example.com
```

## Monitoring & Maintenance

### 1. Application Monitoring

#### View Application Logs
```bash
# Real-time logs
gcloud logs tail --service=default

# Filter logs by severity
gcloud logs read "resource.type=gae_app AND severity>=WARNING" --limit=50

# Search for specific patterns
gcloud logs read "resource.type=gae_app AND textPayload:sync" --limit=20
```

#### Monitor Resource Usage
```bash
# Check App Engine quotas
gcloud app describe

# View instance metrics
gcloud logging read "resource.type=gae_app" \
    --format="table(timestamp,resource.labels.module_id,textPayload)" \
    --limit=10

# Monitor database performance
gcloud sql operations list --instance=boxless-db
```

### 2. Database Maintenance

#### Database Backups
```bash
# Create manual backup
gcloud sql backups create --instance=boxless-db --description="Manual backup $(date)"

# List backups
gcloud sql backups list --instance=boxless-db

# Restore from backup (if needed)
gcloud sql backups restore BACKUP_ID --restore-instance=boxless-db
```

#### Database Performance Monitoring
```bash
# Check database connections
gcloud sql instances describe boxless-db --format="value(settings.ipConfiguration.authorizedNetworks[].value)"

# Monitor slow queries (if enabled)
gcloud sql instances patch boxless-db --database-flags=log_min_duration_statement=1000
```

### 3. Background Task Monitoring

#### Monitor Cloud Tasks
```bash
# List tasks in queue
gcloud tasks list --queue=email-sync-queue --location=$REGION

# Check queue statistics
gcloud tasks queues describe email-sync-queue --location=$REGION

# Purge failed tasks (if needed)
gcloud tasks queues purge email-sync-queue --location=$REGION
```

#### Monitor Cloud Scheduler
```bash
# Check scheduler job status
gcloud scheduler jobs describe periodic-email-sync --location=$REGION

# View job execution history
gcloud logging read "resource.type=cloud_scheduler_job" --limit=10

# Manually trigger job (for testing)
gcloud scheduler jobs run periodic-email-sync --location=$REGION
```

### 4. Performance Optimization

#### Scale App Engine Instances
```bash
# Update scaling configuration
gcloud app deploy --version=scaled --no-promote

# Update app.yaml with new scaling settings:
# automatic_scaling:
#   min_instances: 2
#   max_instances: 20
#   target_cpu_utilization: 0.7
```

#### Database Performance Tuning
```bash
# Upgrade database instance (if needed)
gcloud sql instances patch boxless-db --tier=db-n1-standard-1

# Enable query insights
gcloud sql instances patch boxless-db --insights-config-query-insights-enabled
```

### 5. Security Updates

#### Rotate Secrets
```bash
# Generate new secret key
NEW_SECRET_KEY=$(openssl rand -hex 32)
echo -n "$NEW_SECRET_KEY" | gcloud secrets versions add secret-key --data-file=-

# Update OAuth credentials (when needed)
echo -n "$NEW_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-

# Update database password (more complex process)
# 1. Generate new password
# 2. Update database user
# 3. Update secret
# 4. Redeploy application
```

#### Update Dependencies
```bash
# Update Python packages
pip list --outdated
pip install -r requirements.txt --upgrade

# Update Node.js packages
npm outdated
npm update

# Rebuild and redeploy
npm run build
gcloud app deploy
```

## Troubleshooting

### Common Issues

#### 1. OAuth Redirect URI Mismatch
**Error**: `redirect_uri_mismatch`
**Solution**: 
```bash
# Verify OAuth configuration
gcloud secrets versions access latest --secret=google-client-id
# Update redirect URI in Google Cloud Console to match:
# https://$PROJECT_ID.appspot.com/oauth2/callback
```

#### 2. Database Connection Issues
**Error**: `SQLSTATE[HY000] [2002] Connection refused`
**Solution**:
```bash
# Check Cloud SQL instance status
gcloud sql instances describe boxless-db --format="value(state)"

# Restart if needed
gcloud sql instances restart boxless-db

# Check connection settings in app.yaml
```

#### 3. Background Tasks Not Running
**Error**: Tasks stuck in queue
**Solution**:
```bash
# Check task queue configuration
gcloud tasks queues describe email-sync-queue --location=$REGION

# Check application logs for task handler errors
gcloud logs read "resource.type=gae_app AND textPayload:'/tasks/'" --limit=10

# Purge and recreate queue if necessary
gcloud tasks queues purge email-sync-queue --location=$REGION
```

#### 4. Gmail API Rate Limits
**Error**: `quotaExceeded` or `rateLimitExceeded`
**Solution**:
```bash
# Check API quotas
gcloud services quota list --service=gmail.googleapis.com

# Implement exponential backoff in application code
# Reduce sync frequency if needed
```

#### 5. App Engine Memory Issues
**Error**: `Exceeded soft private memory limit`
**Solution**:
```bash
# Upgrade instance class in app.yaml
# instance_class: F4  # or higher

# Check memory usage patterns
gcloud logging read "resource.type=gae_app AND textPayload:memory" --limit=10
```

### Debug Commands

#### Application Debugging
```bash
# Check application status
gcloud app describe

# View current configuration
gcloud app versions describe v1 --service=default

# Check environment variables
gcloud app versions describe v1 --service=default --format="value(envVariables)"
```

#### Database Debugging
```bash
# Test database connection
gcloud sql connect boxless-db --user=boxless --database=boxless_db

# Check database size
gcloud sql instances describe boxless-db --format="value(settings.dataDiskSizeGb)"

# Monitor active connections
# Run in Cloud SQL proxy or console:
# SELECT count(*) FROM pg_stat_activity;
```

#### Task Queue Debugging
```bash
# Check task execution logs
gcloud logging read "resource.type=cloud_tasks_queue" --limit=20

# Monitor task processing times
gcloud logging read "resource.type=gae_app AND textPayload:'task processing'" --limit=10
```

### Performance Debugging

#### Slow Response Times
```bash
# Analyze request latency
gcloud logging read "resource.type=gae_app" \
    --format="table(timestamp,httpRequest.requestUrl,httpRequest.latency)" \
    --limit=20

# Check database query performance
gcloud sql instances patch boxless-db --database-flags=log_statement=all
```

#### High Resource Usage
```bash
# Monitor CPU usage
gcloud monitoring metrics list --filter="resource.type=gae_app"

# Check memory patterns
gcloud logging read "resource.type=gae_app AND jsonPayload.message:memory" --limit=10
```

## Cost Optimization

### 1. Monitor Costs
```bash
# Check current billing
gcloud billing accounts list
gcloud billing projects describe $PROJECT_ID

# Set up budget alerts
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT \
    --display-name="Boxless Budget" \
    --budget-amount=100USD \
    --threshold-rules-percent=50,75,90,100
```

### 2. Optimize Resource Usage

#### App Engine Optimization
```bash
# Review instance usage
gcloud app instances list

# Optimize scaling settings
# Set min_instances: 0 for development
# Use F1 instance class for low traffic
```

#### Database Optimization
```bash
# Use smaller instance for development
gcloud sql instances patch boxless-db --tier=db-f1-micro

# Enable automatic storage increase
gcloud sql instances patch boxless-db --storage-auto-increase

# Schedule maintenance during low-traffic periods
gcloud sql instances patch boxless-db \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04
```

#### Task Queue Optimization
```bash
# Reduce queue throughput for cost savings
gcloud tasks queues update email-sync-queue \
    --location=$REGION \
    --max-dispatches-per-second=1 \
    --max-concurrent-dispatches=2
```

### 3. Development vs Production

#### Development Environment
```bash
# Use minimal resources for development
export DEV_PROJECT_ID="boxless-dev"

# Create development project with smaller resources
gcloud projects create $DEV_PROJECT_ID
gcloud config set project $DEV_PROJECT_ID

# Deploy with minimal configuration
# - F1 instance class
# - db-f1-micro database
# - Reduced task queue limits
```

#### Production Environment
```bash
# Use optimized resources for production
# - F2+ instance class
# - db-n1-standard-1+ database
# - Higher task queue limits
# - Automated backups
# - Monitoring and alerting
```

### Final Checklist

Before going live:
- [ ] OAuth redirect URIs configured correctly
- [ ] Database backups enabled
- [ ] Monitoring and alerting set up
- [ ] Security secrets rotated
- [ ] Performance testing completed
- [ ] Cost budgets and alerts configured
- [ ] Documentation updated
- [ ] Team access permissions configured

Your Boxless application is now fully deployed and configured for production use on Google Cloud Platform! 🚀

For additional support and advanced configurations, refer to the [Google Cloud Documentation](https://cloud.google.com/docs/) and [Gmail API Documentation](https://developers.google.com/gmail/api).
