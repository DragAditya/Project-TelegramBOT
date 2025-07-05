"""
Database connection and session management for Zultra Telegram Bot.
Handles async database operations with SQLAlchemy.
"""

import asyncio
from typing import AsyncGenerator, Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
)
from sqlalchemy.sql import text
from loguru import logger

from ..core.config import get_settings
from .models import Base

# Global variables
engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker] = None


async def create_engine() -> AsyncEngine:
    """Create and configure the async database engine."""
    settings = get_settings()
    database_url = settings.get_database_url()
    
    # Convert sync URLs to async
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    
    # Engine configuration
    engine_kwargs = {
        "echo": settings.is_debug,
        "future": True,
    }
    
    # SQLite specific settings
    if "sqlite" in database_url:
        engine_kwargs.update({
            "pool_pre_ping": True,
            "connect_args": {"check_same_thread": False}
        })
    else:
        # PostgreSQL settings
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        })
    
    logger.info(f"Creating database engine for: {database_url.split('://')[0]}://...")
    return create_async_engine(database_url, **engine_kwargs)


async def init_db() -> None:
    """Initialize the database connection and create tables."""
    global engine, async_session_maker
    
    try:
        engine = await create_engine()
        async_session_maker = async_sessionmaker(
            engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Test connection
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            await session.commit()
        
        logger.success("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close the database connection."""
    global engine, async_session_maker
    
    if engine:
        await engine.dispose()
        engine = None
        async_session_maker = None
        logger.info("Database connection closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with automatic cleanup."""
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_session_sync() -> AsyncSession:
    """Get an async database session (non-context manager)."""
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    return async_session_maker()


class DatabaseManager:
    """Database manager for handling connections and sessions."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[async_sessionmaker] = None
    
    async def initialize(self) -> None:
        """Initialize database connection."""
        await init_db()
        self.engine = engine
        self.session_maker = async_session_maker
    
    async def close(self) -> None:
        """Close database connection."""
        await close_db()
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        async with get_session() as session:
            yield session
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions
async def get_user_by_id(user_id: int):
    """Get user by Telegram ID."""
    from .models import User
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def get_group_by_id(group_id: int):
    """Get group by Telegram chat ID."""
    from .models import Group
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(Group).where(Group.id == group_id)
        )
        return result.scalar_one_or_none()


async def create_or_update_user(user_data: dict):
    """Create or update a user record."""
    from .models import User
    from sqlalchemy import select
    
    async with get_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.id == user_data['id'])
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
        else:
            # Create new user
            user = User(**user_data)
            session.add(user)
        
        await session.commit()
        await session.refresh(user)
        return user


async def create_or_update_group(group_data: dict):
    """Create or update a group record."""
    from .models import Group
    from sqlalchemy import select
    
    async with get_session() as session:
        # Check if group exists
        result = await session.execute(
            select(Group).where(Group.id == group_data['id'])
        )
        group = result.scalar_one_or_none()
        
        if group:
            # Update existing group
            for key, value in group_data.items():
                if hasattr(group, key):
                    setattr(group, key, value)
        else:
            # Create new group
            group = Group(**group_data)
            session.add(group)
        
        await session.commit()
        await session.refresh(group)
        return group