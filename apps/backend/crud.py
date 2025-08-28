from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
import models

class UserCRUD:
    @staticmethod
    async def create_user(db: AsyncSession, email: str, gmail_user_id: str) -> models.User:
        user = models.User(email=email, gmail_user_id=gmail_user_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
        result = await db.execute(select(models.User).where(models.User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_gmail_id(db: AsyncSession, gmail_user_id: str) -> Optional[models.User]:
        result = await db.execute(select(models.User).where(models.User.gmail_user_id == gmail_user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_tokens(db: AsyncSession, user_id: int, access_token: str, refresh_token: str, expiry: datetime):
        result = await db.execute(select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.token_expiry = expiry
            await db.commit()
            await db.refresh(user)
        return user

class EmailCRUD:
    @staticmethod
    async def create_email(db: AsyncSession, email_data: dict, user_id: int) -> models.Email:
        email = models.Email(
            gmail_message_id=email_data['id'],
            thread_id=email_data.get('threadId'),
            subject=email_data.get('subject'),
            sender=email_data.get('sender'),
            recipient=email_data.get('recipient'),
            date_sent=email_data.get('date_sent'),
            date_received=email_data.get('date_received'),
            body_text=email_data.get('body_text'),
            body_html=email_data.get('body_html'),
            snippet=email_data.get('snippet'),
            is_read=email_data.get('is_read', False),
            raw_headers=email_data.get('headers'),
            user_id=user_id
        )
        db.add(email)
        await db.commit()
        await db.refresh(email)
        return email
    
    @staticmethod
    async def get_emails_by_user(db: AsyncSession, user_id: int, limit: int = 50) -> List[models.Email]:
        result = await db.execute(
            select(models.Email)
            .where(models.Email.user_id == user_id)
            .order_by(models.Email.date_received.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_email_by_gmail_id(db: AsyncSession, gmail_message_id: str) -> Optional[models.Email]:
        result = await db.execute(
            select(models.Email).where(models.Email.gmail_message_id == gmail_message_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def email_exists(db: AsyncSession, gmail_message_id: str) -> bool:
        result = await db.execute(
            select(models.Email).where(models.Email.gmail_message_id == gmail_message_id)
        )
        return result.scalar_one_or_none() is not None

class LabelCRUD:
    @staticmethod
    async def create_label(db: AsyncSession, label_data: dict, user_id: int) -> models.Label:
        label = models.Label(
            gmail_label_id=label_data['id'],
            name=label_data['name'],
            label_type=label_data.get('type', 'user'),
            messages_total=label_data.get('messagesTotal', 0),
            messages_unread=label_data.get('messagesUnread', 0),
            user_id=user_id
        )
        db.add(label)
        await db.commit()
        await db.refresh(label)
        return label
    
    @staticmethod
    async def get_labels_by_user(db: AsyncSession, user_id: int) -> List[models.Label]:
        result = await db.execute(
            select(models.Label).where(models.Label.user_id == user_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_label_by_gmail_id(db: AsyncSession, gmail_label_id: str, user_id: int) -> Optional[models.Label]:
        result = await db.execute(
            select(models.Label).where(
                and_(models.Label.gmail_label_id == gmail_label_id, models.Label.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

class SyncCRUD:
    @staticmethod
    async def create_sync_status(db: AsyncSession, user_id: int) -> models.SyncStatus:
        sync_status = models.SyncStatus(user_id=user_id)
        db.add(sync_status)
        await db.commit()
        await db.refresh(sync_status)
        return sync_status
    
    @staticmethod
    async def update_sync_status(db: AsyncSession, user_id: int, status: str, emails_synced: int = None, error_message: str = None):
        result = await db.execute(select(models.SyncStatus).where(models.SyncStatus.user_id == user_id))
        sync_status = result.scalar_one_or_none()
        
        if sync_status:
            sync_status.sync_status = status
            sync_status.last_sync = datetime.utcnow()
            if emails_synced is not None:
                sync_status.emails_synced = emails_synced
            if error_message:
                sync_status.error_message = error_message
            await db.commit()
            await db.refresh(sync_status)
        
        return sync_status

# Helper functions for sync operations
async def sync_emails_to_db(db: AsyncSession, user_id: int, emails_data: List[dict]) -> dict:
    """Sync emails to database"""
    created_count = 0
    updated_count = 0
    
    for email_data in emails_data:
        existing = await EmailCRUD.get_email_by_gmail_id(db, email_data['id'])
        
        if not existing:
            await EmailCRUD.create_email(db, email_data, user_id)
            created_count += 1
        else:
            # Update existing email if needed
            updated_count += 1
    
    return {
        "created": created_count,
        "updated": updated_count,
        "total": len(emails_data)
    }

async def sync_labels_to_db(db: AsyncSession, user_id: int, labels_data: List[dict]) -> dict:
    """Sync labels to database"""
    created_count = 0
    
    for label_data in labels_data:
        existing = await LabelCRUD.get_label_by_gmail_id(db, label_data['id'], user_id)
        
        if not existing:
            await LabelCRUD.create_label(db, label_data, user_id)
            created_count += 1
    
    return {
        "created": created_count,
        "total": len(labels_data)
    }
