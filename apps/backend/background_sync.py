"""Background task management for email synchronization"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.cloud import tasks_v2
from google.oauth2.credentials import Credentials

from database import AsyncSessionLocal
from models import User, SyncStatus
from gmail_service import GmailService
from crud import UserCRUD, sync_emails_to_db, sync_labels_to_db, SyncCRUD

logger = logging.getLogger(__name__)

class BackgroundSyncManager:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        self.queue_name = 'email-sync-queue'
        
        # Initialize Cloud Tasks client
        if self.project_id:
            self.tasks_client = tasks_v2.CloudTasksClient()
            self.parent = self.tasks_client.queue_path(
                self.project_id, self.location, self.queue_name
            )
    
    async def schedule_user_sync(self, user_id: int, delay_seconds: int = 0):
        """Schedule a sync task for a specific user"""
        if not self.project_id:
            # Local development - run sync immediately
            await self.sync_user_emails(user_id)
            return
        
        # Create Cloud Task
        task = {
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'url': f'https://{self.project_id}.appspot.com/tasks/sync-user',
                'headers': {'Content-Type': 'application/json'},
                'body': f'{{"user_id": {user_id}}}'.encode(),
            }
        }
        
        if delay_seconds > 0:
            timestamp = datetime.utcnow() + timedelta(seconds=delay_seconds)
            task['schedule_time'] = timestamp
        
        # Submit task
        response = self.tasks_client.create_task(
            request={'parent': self.parent, 'task': task}
        )
        
        logger.info(f"Scheduled sync task for user {user_id}: {response.name}")
    
    async def sync_user_emails(self, user_id: int) -> dict:
        """Sync emails for a specific user"""
        async with AsyncSessionLocal() as db:
            try:
                # Update sync status to 'running'
                await SyncCRUD.update_sync_status(
                    db, user_id, 'running', error_message=None
                )
                
                # Get user
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                
                if not user:
                    raise Exception(f"User {user_id} not found")
                
                if not user.access_token:
                    raise Exception(f"User {user_id} has no access token")
                
                # Create Gmail service with user's credentials
                gmail_service = GmailService()
                
                # Reconstruct credentials
                creds = Credentials(
                    token=user.access_token,
                    refresh_token=user.refresh_token,
                    token_expiry=user.token_expiry
                )
                
                # Set credentials manually
                gmail_service._credentials = creds
                
                # Sync labels first
                labels = gmail_service.get_labels()
                label_sync_result = await sync_labels_to_db(db, user.id, labels)
                
                # Sync emails in batches
                total_synced = 0
                batch_size = 100
                max_results = 1000  # Limit for initial sync
                
                # Get emails in batches
                for page in range(0, max_results, batch_size):
                    try:
                        emails = gmail_service.get_emails(
                            max_results=min(batch_size, max_results - page),
                            query='newer_than:30d'  # Only recent emails to avoid timeouts
                        )
                        
                        if not emails:
                            break
                        
                        email_sync_result = await sync_emails_to_db(db, user.id, emails)
                        total_synced += email_sync_result['created']
                        
                        # Small delay between batches
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error syncing batch for user {user_id}: {e}")
                        break
                
                # Update sync status to 'completed'
                await SyncCRUD.update_sync_status(
                    db, user_id, 'completed', emails_synced=total_synced
                )
                
                result = {
                    'user_id': user_id,
                    'status': 'completed',
                    'emails_synced': total_synced,
                    'labels_synced': label_sync_result['created']
                }
                
                logger.info(f"Completed sync for user {user_id}: {total_synced} emails")
                return result
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Sync failed for user {user_id}: {error_msg}")
                
                # Update sync status to 'failed'
                await SyncCRUD.update_sync_status(
                    db, user_id, 'failed', error_message=error_msg
                )
                
                return {
                    'user_id': user_id,
                    'status': 'failed',
                    'error': error_msg
                }
    
    async def sync_all_active_users(self):
        """Sync emails for all active users"""
        async with AsyncSessionLocal() as db:
            # Get all active users with valid tokens
            result = await db.execute(
                select(User).where(
                    User.is_active == True,
                    User.access_token.isnot(None)
                )
            )
            users = result.scalars().all()
            
            logger.info(f"Starting background sync for {len(users)} users")
            
            for i, user in enumerate(users):
                try:
                    # Schedule sync with staggered delays to avoid rate limits
                    delay = i * 30  # 30 seconds between each user sync
                    await self.schedule_user_sync(user.id, delay_seconds=delay)
                    
                except Exception as e:
                    logger.error(f"Failed to schedule sync for user {user.id}: {e}")
    
    async def cleanup_old_sync_statuses(self, days: int = 7):
        """Clean up old sync status records"""
        async with AsyncSessionLocal() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old sync statuses
            await db.execute(
                "DELETE FROM sync_statuses WHERE last_sync < :cutoff",
                {"cutoff": cutoff_date}
            )
            await db.commit()

# Global instance
sync_manager = BackgroundSyncManager()
