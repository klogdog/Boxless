import os
import json
import base64
from typing import List, Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import pickle
from datetime import datetime


class GmailService:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        self.credentials_file = 'credentials.json'
        self.token_file = 'token.pickle'
        self.redirect_uri = 'http://127.0.0.1:8000/oauth2/callback'
        
    def get_authorization_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return authorization_url
    
    def handle_oauth_callback(self, authorization_code: str):
        """Handle OAuth callback and save credentials"""
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        flow.fetch_token(code=authorization_code)
        
        # Save credentials
        with open(self.token_file, 'wb') as token:
            pickle.dump(flow.credentials, token)
    
    def get_credentials(self) -> Credentials:
        """Get valid credentials"""
        creds = None
        
        # Load existing credentials
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        if not creds or not creds.valid:
            raise Exception("No valid credentials available. Please authenticate first.")
        
        return creds
    
    def get_service(self):
        """Get Gmail API service"""
        creds = self.get_credentials()
        return build('gmail', 'v1', credentials=creds)
    
    def get_emails(self, query: Optional[str] = None, max_results: int = 10, label_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch emails from Gmail"""
        service = self.get_service()
        
        # Build query parameters
        params = {
            'userId': 'me',
            'maxResults': max_results
        }
        
        if query:
            params['q'] = query
        
        if label_ids:
            params['labelIds'] = label_ids
        
        # Get message list
        results = service.users().messages().list(**params).execute()
        messages = results.get('messages', [])
        
        emails = []
        for message in messages:
            # Get full message details
            msg = service.users().messages().get(
                userId='me', 
                id=message['id'],
                format='full'
            ).execute()
            
            email_data = self._parse_email(msg)
            emails.append(email_data)
        
        return emails
    
    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message into structured data"""
        payload = message['payload']
        headers = payload.get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        # Extract body
        body = self._extract_body(payload)
        
        # Get labels
        labels = message.get('labelIds', [])
        
        return {
            'id': message['id'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
            'labels': labels
        }
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            # Multi-part message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            # Single part message
            if payload['mimeType'] in ['text/plain', 'text/html']:
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def get_labels(self) -> List[Dict[str, str]]:
        """Get Gmail labels"""
        service = self.get_service()
        
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        return [{'id': label['id'], 'name': label['name']} for label in labels]
    
    def get_single_email(self, email_id: str) -> Dict[str, Any]:
        """Get a single email by ID"""
        service = self.get_service()
        
        # Get full message details
        msg = service.users().messages().get(
            userId='me', 
            id=email_id,
            format='full'
        ).execute()
        
        return self._parse_email(msg)
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email"""
        service = self.get_service()
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return send_message
