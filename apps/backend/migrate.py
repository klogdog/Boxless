"""Database migration script for production deployment"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from database import Base
from models import User, Email, Label, Attachment, SyncStatus

async def run_migrations():
    """Run database migrations"""
    # Get database URL from environment
    database_url = os.getenv('ASYNC_DATABASE_URL') or os.getenv('DATABASE_URL')
    
    if not database_url:
        print("Error: No database URL found in environment variables")
        sys.exit(1)
    
    # Convert PostgreSQL URL to async if needed
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    print(f"Connecting to database...")
    
    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        sys.exit(1)
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migrations())
