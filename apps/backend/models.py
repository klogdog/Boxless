from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    gmail_user_id = Column(String, unique=True, index=True)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    emails = relationship("Email", back_populates="user")
    labels = relationship("Label", back_populates="user")
    sync_status = relationship("SyncStatus", back_populates="user")

class Label(Base):
    __tablename__ = "labels"
    
    id = Column(Integer, primary_key=True, index=True)
    gmail_label_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    label_type = Column(String)  # system, user
    messages_total = Column(Integer, default=0)
    messages_unread = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="labels")
    emails = relationship("EmailLabel", back_populates="label")

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    gmail_message_id = Column(String, unique=True, index=True, nullable=False)
    thread_id = Column(String, index=True)
    subject = Column(Text)
    sender = Column(String)
    recipient = Column(String)
    cc = Column(Text)
    bcc = Column(Text)
    date_sent = Column(DateTime)
    date_received = Column(DateTime)
    body_text = Column(Text)
    body_html = Column(Text)
    snippet = Column(Text)
    is_read = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    raw_headers = Column(JSON)
    attachments_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="emails")
    labels = relationship("EmailLabel", back_populates="email")
    attachments = relationship("Attachment", back_populates="email")

class EmailLabel(Base):
    __tablename__ = "email_labels"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    label_id = Column(Integer, ForeignKey("labels.id"))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    email = relationship("Email", back_populates="labels")
    label = relationship("Label", back_populates="emails")

class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String)
    size = Column(Integer)
    attachment_id = Column(String)  # Gmail attachment ID
    email_id = Column(Integer, ForeignKey("emails.id"))
    file_path = Column(String)  # Local storage path
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    email = relationship("Email", back_populates="attachments")

class SyncStatus(Base):
    __tablename__ = "sync_status"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    last_sync = Column(DateTime)
    last_history_id = Column(String)
    emails_synced = Column(Integer, default=0)
    sync_status = Column(String, default="pending")  # pending, running, completed, error
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sync_status")
