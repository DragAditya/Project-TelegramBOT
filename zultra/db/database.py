"""
Database connection and session management for Zultra Telegram Bot.
Handles async database operations with SQLAlchemy.
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from loguru import logger

from ..core.config import get_settings
from .models import Base

# Global variables
engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker] = None
settings = get_settings()


async def create_engine() -> AsyncEngine:
    """Create and configure the async database engine."""
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
        "pool_pre_ping": True,
    }
    
    # Production-specific settings
    if settings.is_production:
        engine_kwargs.update({
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 3600,
        })
    else:
        # Development settings
        engine_kwargs.update({
            "pool_size": 5,
            "max_overflow": 10,
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
    
    async def backup_database(self, backup_path: str) -> bool:
        """Create a database backup (SQLite only for now)."""
        try:
            if "sqlite" in settings.database_url:
                import shutil
                import os
                
                db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
                if os.path.exists(db_path):
                    shutil.copy2(db_path, backup_path)
                    logger.info(f"Database backed up to: {backup_path}")
                    return True
            else:
                logger.warning("Database backup not implemented for PostgreSQL")
                return False
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    async def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup (SQLite only for now)."""
        try:
            if "sqlite" in settings.database_url:
                import shutil
                import os
                
                db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
                if os.path.exists(backup_path):
                    # Close existing connections
                    await self.close()
                    
                    # Restore backup
                    shutil.copy2(backup_path, db_path)
                    
                    # Reinitialize
                    await self.initialize()
                    
                    logger.info(f"Database restored from: {backup_path}")
                    return True
            else:
                logger.warning("Database restore not implemented for PostgreSQL")
                return False
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (convenience function)."""
    async with get_session() as session:
        yield session


async def execute_query(query: str, **params) -> list:
    """Execute a raw SQL query and return results."""
    async with get_session() as session:
        result = await session.execute(text(query), params)
        return result.fetchall()


async def get_user_by_id(user_id: int) -> Optional['User']:
    """Get user by Telegram ID."""
    from .models import User
    
    async with get_session() as session:
        result = await session.get(User, user_id)
        return result


async def get_group_by_id(group_id: int) -> Optional['Group']:
    """Get group by Telegram chat ID."""
    from .models import Group
    
    async with get_session() as session:
        result = await session.get(Group, group_id)
        return result


async def create_or_update_user(user_data: dict) -> 'User':
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


async def create_or_update_group(group_data: dict) -> 'Group':
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