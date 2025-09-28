#!/usr/bin/env python3
"""Database setup script"""

import asyncio
import asyncpg
import os
from sqlalchemy.ext.asyncio import create_async_engine
from src.infrastructure.database.models import Base

async def create_database():
    """Create database and tables"""
    database_url = os.getenv("DATABASE_URL", "postgresql://trackinguser:trackingpass@localhost/tracking_db")
    
    # Create engine
    engine = create_async_engine(database_url)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database setup completed!")

if __name__ == "__main__":
    asyncio.run(create_database())