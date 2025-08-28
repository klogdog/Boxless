from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import select

from gmail_service import GmailService
from database import get_db, get_async_db
from models import User, Email, Label, Attachment
from crud import UserCRUD, EmailCRUD, LabelCRUD, sync_emails_to_db, sync_labels_to_db

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

# Database sync endpoints
@app.post("/gmail/sync")
async def sync_gmail_data(db = Depends(get_async_db)):
    """Sync Gmail data to local database"""
    try:
        gmail_service = GmailService()
        
        # Get user info from Gmail (you might want to store user session)
        profile = gmail_service.get_profile()
        user_email = profile.get('emailAddress')
        
        if not user_email:
            raise HTTPException(status_code=400, detail="Could not get user email from Gmail")
        
        # Get or create user
        user = await UserCRUD.get_user_by_email(db, user_email)
        if not user:
            # Use email as gmail_user_id if no separate ID is available
            gmail_user_id = profile.get('emailAddress', user_email)
            user = await UserCRUD.create_user(db, user_email, gmail_user_id)
        
        # Sync labels
        labels = gmail_service.get_labels()
        label_sync_result = await sync_labels_to_db(db, user.id, labels)
        
        # Sync emails (get recent emails)
        emails = gmail_service.get_emails(max_results=50)
        email_sync_result = await sync_emails_to_db(db, user.id, emails)
        
        return {
            "message": "Sync completed successfully",
            "user_email": user_email,
            "labels": label_sync_result,
            "emails": email_sync_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/emails")
async def get_stored_emails(limit: int = 50, db = Depends(get_async_db)):
    """Get emails from local database"""
    try:
        # For now, get the first user (in a real app, you'd use session management)
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="No user found. Please sync data first.")
        
        emails = await EmailCRUD.get_emails_by_user(db, user.id, limit)
        
        # Convert to dict format
        email_list = []
        for email in emails:
            email_list.append({
                "id": email.gmail_message_id,
                "subject": email.subject,
                "sender": email.sender,
                "date": email.date_received.isoformat() if email.date_received else None,
                "body": email.snippet,
                "is_read": email.is_read
            })
        
        return {"emails": email_list, "total": len(email_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
