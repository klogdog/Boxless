# Gmail API Setup Instructions

## 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

## 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://127.0.0.1:8000/gmail/callback`
5. Download the credentials file as `credentials.json`
6. Place it in the `/apps/backend/` directory

## 3. Environment Setup

1. Copy `.env.example` to `.env`
2. Fill in your Google Client ID and Secret from the credentials file

## 4. Install Dependencies

```bash
cd apps/backend
poetry install
```

## 5. Run the Backend

```bash
cd apps/backend
poetry run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 6. Authentication Flow

1. Visit `http://127.0.0.1:8000/gmail/auth-url` to get the authorization URL
2. Follow the OAuth flow
3. The callback will handle the authorization code
4. You can then fetch emails using the `/gmail/emails` endpoint

## API Endpoints

- `GET /gmail/auth-url` - Get OAuth authorization URL
- `POST /gmail/callback?code=...` - Handle OAuth callback
- `POST /gmail/emails` - Fetch emails (with optional query parameters)
- `GET /gmail/labels` - Get Gmail labels

## Example Usage

```python
import requests

# Get auth URL
response = requests.get("http://127.0.0.1:8000/gmail/auth-url")
auth_url = response.json()["auth_url"]
print(f"Visit: {auth_url}")

# After authentication, fetch emails
email_query = {
    "query": "is:unread",
    "max_results": 20
}
response = requests.post("http://127.0.0.1:8000/gmail/emails", json=email_query)
emails = response.json()
```
