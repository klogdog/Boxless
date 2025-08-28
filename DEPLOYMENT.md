# 🚀 Boxless - Google Cloud Deployment Guide

## Overview

Boxless is now configured for production deployment on Google Cloud Platform with automated background email synchronization. The system includes:

- **FastAPI Backend** with Gmail API integration
- **Vue.js Frontend** with OAuth flow
- **PostgreSQL Database** on Cloud SQL
- **Background Tasks** using Cloud Tasks
- **Scheduled Sync** using Cloud Scheduler
- **Automated Deployment** using Cloud Build

## 📋 Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Gmail API Credentials** (OAuth 2.0 Client ID)
3. **Google Cloud SDK** installed locally
4. **Node.js 18+** and **Python 3.11+**

## 🏗️ Quick Deployment

### 1. Setup Google Cloud Infrastructure

```bash
# Run the automated setup script
./setup-gcloud.sh
```

This script will:
- Enable required Google Cloud APIs
- Create Cloud SQL PostgreSQL instance
- Create App Engine application
- Set up Cloud Tasks queue
- Configure Cloud Scheduler for periodic sync
- Create secrets in Secret Manager

### 2. Configure OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Create OAuth 2.0 Client ID for web application
4. Add authorized redirect URI: `https://YOUR-PROJECT-ID.appspot.com/oauth2/callback`

### 3. Update Configuration

Edit `app.yaml` and replace placeholders:
```yaml
env_variables:
  # Replace with your values
  PROJECT_ID: your-project-id
  REGION: us-central1
  DB_PASSWORD: your-secure-password
  GOOGLE_CLIENT_ID: your-client-id.googleusercontent.com
  GOOGLE_CLIENT_SECRET: your-client-secret
  SECRET_KEY: your-32-character-secret-key
```

### 4. Build and Deploy

```bash
# Build frontend
cd apps/frontend
npm install
npm run build

# Deploy to App Engine
cd ../..
gcloud app deploy
```

## 🔧 Configuration Details

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID | ✅ |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret | ✅ |
| `SECRET_KEY` | Application secret key | ✅ |
| `ENABLE_BACKGROUND_SYNC` | Enable background tasks | ✅ |
| `SYNC_INTERVAL_MINUTES` | Sync frequency (default: 30) | ❌ |

### Database Schema

The application automatically creates these tables:
- `users` - User accounts and OAuth tokens
- `emails` - Synchronized email content
- `labels` - Gmail labels/folders
- `attachments` - Email attachments metadata
- `sync_statuses` - Background sync tracking

### Background Sync Features

1. **Manual Sync**: Quick sync of recent emails (50 emails)
2. **Background Sync**: Full sync of all user emails without frontend
3. **Scheduled Sync**: Automatic sync every 6 hours
4. **Batch Processing**: Handles large volumes with rate limiting
5. **Error Recovery**: Automatic retry on failures

## 🔒 Security Features

- **OAuth 2.0** for secure Gmail access
- **Cloud SQL** with encrypted connections
- **Secret Manager** for sensitive configuration
- **CORS** protection for API endpoints
- **Token refresh** handling

## 📊 Monitoring & Logging

### Cloud Logging

View application logs:
```bash
gcloud logs tail --service=default
```

### Sync Status Monitoring

Check sync status via API:
```bash
curl https://YOUR-PROJECT-ID.appspot.com/sync/status/USER_ID
```

### Cloud Tasks Queue

Monitor background tasks:
```bash
gcloud tasks list --queue=email-sync-queue --location=us-central1
```

## 🚀 Usage

### 1. User Authentication
- Users visit your deployed app
- Click "Connect Gmail Account"
- Complete OAuth flow
- Tokens stored securely in database

### 2. Email Synchronization

**Quick Sync** (Frontend):
- Limited to recent emails
- Requires frontend to be open
- Good for immediate testing

**Background Sync** (Automated):
- Syncs ALL user emails
- Runs in background
- No frontend required
- Scheduled automatically

### 3. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/gmail/auth-url` | GET | Get OAuth URL |
| `/oauth2/callback` | GET | OAuth callback |
| `/gmail/sync` | POST | Quick sync |
| `/gmail/sync-background` | POST | Start background sync |
| `/db/emails` | GET | Get stored emails |
| `/sync/status/{user_id}` | GET | Check sync status |

## 🔄 Automated Features

### Scheduled Background Sync
- **Frequency**: Every 6 hours
- **Scope**: All active users
- **Batching**: 30-second delays between users
- **Rate Limiting**: Respects Gmail API limits

### Error Handling
- **Retry Logic**: Failed syncs are retried
- **Error Logging**: All errors logged to Cloud Logging
- **Status Tracking**: Sync status stored in database

### Token Management
- **Automatic Refresh**: Expired tokens refreshed automatically
- **Secure Storage**: Tokens encrypted in Cloud SQL
- **Cleanup**: Old tokens cleaned up periodically

## 📈 Scaling Considerations

### Performance
- **Cloud SQL**: Auto-scaling storage
- **App Engine**: Auto-scaling instances (1-10)
- **Cloud Tasks**: Handles high throughput
- **Batch Processing**: Efficient email handling

### Cost Optimization
- **F2 Instance Class**: Cost-effective for most workloads
- **Micro Cloud SQL**: Minimal database tier
- **Scheduled Scaling**: Automatic instance scaling

## 🛠️ Maintenance

### Database Migrations
```bash
# Run migrations manually
gcloud app deploy --version=migration
```

### Update Dependencies
```bash
# Update Python packages
pip install -r requirements.txt --upgrade

# Update Node packages
npm update
```

### Monitor Resource Usage
```bash
# Check App Engine quotas
gcloud app describe

# Check Cloud SQL metrics
gcloud sql instances describe boxless-db
```

## 🐛 Troubleshooting

### Common Issues

1. **OAuth Errors**: Check redirect URI configuration
2. **Database Connection**: Verify Cloud SQL proxy setup
3. **Task Queue Errors**: Check Cloud Tasks permissions
4. **Rate Limiting**: Gmail API has usage limits

### Debug Commands
```bash
# Check application status
gcloud app browse

# View recent logs
gcloud logs read --service=default --limit=50

# Check task queue
gcloud tasks list --queue=email-sync-queue --location=us-central1
```

## 📞 Support

For issues or questions:
1. Check Cloud Logging for error details
2. Review API quotas and limits
3. Verify OAuth configuration
4. Check database connectivity

## 🎯 Next Steps

After deployment:
1. Test OAuth flow with your Gmail account
2. Start a background sync
3. Monitor sync status and logs
4. Set up additional monitoring as needed
5. Configure custom sync schedules if required

Your Boxless application is now ready for production use with automated email synchronization! 🚀
