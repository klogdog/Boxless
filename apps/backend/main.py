from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from gmail_service import GmailService

load_dotenv()

app = FastAPI(title="Boxless Backend", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EmailData(BaseModel):
    id: str
    subject: str
    sender: str
    date: str
    body: Optional[str] = None
    labels: List[str] = []

class EmailQuery(BaseModel):
    query: Optional[str] = None
    max_results: Optional[int] = 10
    label_ids: Optional[List[str]] = None

@app.get("/")
async def root():
    return {"message": "Welcome to Boxless Backend"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/gmail/auth-url")
async def get_auth_url():
    """Get Google OAuth authorization URL"""
    try:
        gmail_service = GmailService()
        auth_url = gmail_service.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth2/callback")
async def handle_oauth_callback(code: str):
    """Handle OAuth callback and store credentials"""
    try:
        gmail_service = GmailService()
        gmail_service.handle_oauth_callback(code)
        
        # Return HTML that closes the popup and notifies parent
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Authentication</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .success { color: #28a745; }
            </style>
        </head>
        <body>
            <div class="success">
                <h2>✓ Authentication Successful!</h2>
                <p>You can close this window.</p>
            </div>
            <script>
                // Notify parent window and close popup
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'GMAIL_AUTH_SUCCESS'
                    }, '*');
                }
                setTimeout(() => window.close(), 2000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        # Return error HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Authentication Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>⚠ Authentication Failed</h2>
                <p>Error: {str(e)}</p>
                <p>You can close this window and try again.</p>
            </div>
            <script>
                setTimeout(() => window.close(), 5000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content, status_code=400)

@app.post("/gmail/emails", response_model=List[EmailData])
async def get_emails(query: EmailQuery):
    """Fetch emails from Gmail"""
    try:
        gmail_service = GmailService()
        emails = gmail_service.get_emails(
            query=query.query,
            max_results=query.max_results,
            label_ids=query.label_ids
        )
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gmail/labels")
async def get_labels():
    """Get Gmail labels"""
    try:
        gmail_service = GmailService()
        labels = gmail_service.get_labels()
        return {"labels": labels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gmail/email/{email_id}")
async def get_single_email(email_id: str):
    """Get a single email by ID"""
    try:
        gmail_service = GmailService()
        email = gmail_service.get_single_email(email_id)
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
