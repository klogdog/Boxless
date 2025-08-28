#!/usr/bin/env python3
"""Script to create database tables"""

import asyncio
from database import async_engine, Base
from models import User, Email, Label, Attachment  # Import all models

async def create_tables():
    """Create all tables in the database"""
    async with async_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
