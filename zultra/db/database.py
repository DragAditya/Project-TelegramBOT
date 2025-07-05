"""
Production-ready database connection and session management for Zultra Telegram Bot.
Bulletproof async database operations with comprehensive error handling.
"""

import asyncio
import time
from typing import AsyncGenerator, Optional, Dict, Any, Union
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
)
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError
from sqlalchemy.pool import StaticPool
from loguru import logger

from ..core.config import get_settings
from .models import Base


class DatabaseConnectionError(Exception):
    """Database connection related errors."""
    pass


class DatabaseManager:
    """Production-ready database manager with error handling and recovery."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[async_sessionmaker] = None
        self.is_initialized = False
        self.connection_retries = 0
        self.max_retries = 5
        self.retry_delay = 1.0
        
    async def initialize(self) -> bool:
        """Initialize database with comprehensive error handling."""
        settings = get_settings()
        
        for attempt in range(self.max_retries):
            try:
                # Create engine
                self.engine = await self._create_engine()
                
                # Create session maker
                self.session_maker = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=True,
                    autocommit=False
                )
                
                # Create tables
                await self._create_tables()
                
                # Test connection
                await self._test_connection()
                
                self.is_initialized = True
                self.connection_retries = 0
                logger.success("Database initialized successfully")
                return True
                
            except Exception as e:
                self.connection_retries += 1
                logger.error(f"Database initialization attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.critical("Database initialization failed after all retries")
                    return False
        
        return False
    
    async def _create_engine(self) -> AsyncEngine:
        """Create database engine with appropriate settings."""
        settings = get_settings()
        database_url = settings.database_url
        
        # Convert sync URLs to async
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        
        # Base engine configuration
        engine_kwargs = {
            "echo": settings.is_debug,
            "future": True,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections every hour
        }
        
        # Database-specific configurations
        if "sqlite" in database_url:
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30
                }
            })
        else:
            # PostgreSQL configuration
            engine_kwargs.update({
                "pool_size": settings.connection_pool_size,
                "max_overflow": settings.connection_pool_size * 2,
                "pool_timeout": 30,
                "connect_args": {
                    "server_settings": {
                        "application_name": "zultra_bot",
                    },
                    "command_timeout": 30,
                }
            })
        
        logger.info(f"Creating database engine: {database_url.split('://')[0]}://...")
        return create_async_engine(database_url, **engine_kwargs)
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise DatabaseConnectionError(f"Table creation failed: {e}")
    
    async def _test_connection(self) -> None:
        """Test database connection."""
        try:
            async with self.session_maker() as session:
                result = await session.execute(text("SELECT 1"))
                row = result.fetchone()
                if row[0] != 1:
                    raise DatabaseConnectionError("Connection test failed")
            logger.info("Database connection test passed")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise DatabaseConnectionError(f"Connection test failed: {e}")
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            try:
                await self.engine.dispose()
                logger.info("Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")
            finally:
                self.engine = None
                self.session_maker = None
                self.is_initialized = False
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with comprehensive error handling."""
        if not self.is_initialized:
            raise DatabaseConnectionError("Database not initialized")
        
        session = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                session = self.session_maker()
                yield session
                await session.commit()
                return
                
            except DisconnectionError as e:
                logger.warning(f"Database disconnection detected: {e}")
                if session:
                    await session.rollback()
                    await session.close()
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    await self._reconnect()
                else:
                    raise DatabaseConnectionError("Database disconnected and reconnection failed")
            
            except TimeoutError as e:
                logger.warning(f"Database timeout: {e}")
                if session:
                    await session.rollback()
                    await session.close()
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                else:
                    raise DatabaseConnectionError("Database operation timed out")
            
            except SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                if session:
                    try:
                        await session.rollback()
                    except Exception:
                        pass
                    await session.close()
                raise
            
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                if session:
                    try:
                        await session.rollback()
                    except Exception:
                        pass
                    await session.close()
                raise
            
            finally:
                if session:
                    try:
                        await session.close()
                    except Exception as e:
                        logger.error(f"Error closing session: {e}")
    
    async def _reconnect(self) -> None:
        """Attempt to reconnect to database."""
        try:
            if self.engine:
                await self.engine.dispose()
            
            # Reinitialize
            await self.initialize()
            logger.info("Database reconnection successful")
            
        except Exception as e:
            logger.error(f"Database reconnection failed: {e}")
            raise DatabaseConnectionError("Failed to reconnect to database")
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        if not self.is_initialized:
            return {
                "status": "unhealthy",
                "error": "Database not initialized",
                "connection_retries": self.connection_retries
            }
        
        try:
            start_time = time.time()
            
            async with self.session() as session:
                # Test basic query
                result = await session.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                
                # Test write operation
                await session.execute(text("CREATE TEMP TABLE IF NOT EXISTS health_check (id INTEGER)"))
                await session.execute(text("INSERT INTO health_check (id) VALUES (1)"))
                
                response_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "connection_retries": self.connection_retries,
                    "pool_size": getattr(self.engine.pool, 'size', 'N/A'),
                    "checked_out_connections": getattr(self.engine.pool, 'checkedout', 'N/A'),
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_retries": self.connection_retries
            }
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Execute raw SQL query safely."""
        try:
            async with self.session() as session:
                result = await session.execute(text(query), params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def backup_database(self, backup_path: str) -> bool:
        """Create database backup (SQLite only)."""
        settings = get_settings()
        
        if "sqlite" not in settings.database_url:
            logger.warning("Backup only supported for SQLite databases")
            return False
        
        try:
            import shutil
            import os
            
            # Extract database path
            db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
            
            if os.path.exists(db_path):
                # Ensure backup directory exists
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                
                # Create backup
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backed up to: {backup_path}")
                return True
            else:
                logger.error(f"Database file not found: {db_path}")
                return False
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False


# Global database manager
db_manager = DatabaseManager()


# Convenience functions with error handling
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with db_manager.session() as session:
        yield session


async def init_db() -> bool:
    """Initialize database."""
    return await db_manager.initialize()


async def close_db() -> None:
    """Close database connections."""
    await db_manager.close()


# Model helper functions
async def get_user_by_id(user_id: int):
    """Get user by Telegram ID with error handling."""
    try:
        from .models import User
        from sqlalchemy import select
        
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
            
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


async def get_group_by_id(group_id: int):
    """Get group by Telegram chat ID with error handling."""
    try:
        from .models import Group
        from sqlalchemy import select
        
        async with get_session() as session:
            result = await session.execute(
                select(Group).where(Group.id == group_id)
            )
            return result.scalar_one_or_none()
            
    except Exception as e:
        logger.error(f"Error getting group {group_id}: {e}")
        return None


async def create_or_update_user(user_data: dict):
    """Create or update user with comprehensive error handling."""
    try:
        from .models import User
        from sqlalchemy import select
        
        # Validate required fields
        if 'id' not in user_data:
            raise ValueError("User ID is required")
        
        async with get_session() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.id == user_data['id'])
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Update existing user
                for key, value in user_data.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)
                logger.debug(f"Updated user {user_data['id']}")
            else:
                # Create new user
                user = User(**user_data)
                session.add(user)
                logger.debug(f"Created new user {user_data['id']}")
            
            await session.commit()
            await session.refresh(user)
            return user
            
    except Exception as e:
        logger.error(f"Error creating/updating user: {e}")
        return None


async def create_or_update_group(group_data: dict):
    """Create or update group with comprehensive error handling."""
    try:
        from .models import Group
        from sqlalchemy import select
        
        # Validate required fields
        if 'id' not in group_data:
            raise ValueError("Group ID is required")
        
        async with get_session() as session:
            # Check if group exists
            result = await session.execute(
                select(Group).where(Group.id == group_data['id'])
            )
            group = result.scalar_one_or_none()
            
            if group:
                # Update existing group
                for key, value in group_data.items():
                    if hasattr(group, key) and value is not None:
                        setattr(group, key, value)
                logger.debug(f"Updated group {group_data['id']}")
            else:
                # Create new group
                group = Group(**group_data)
                session.add(group)
                logger.debug(f"Created new group {group_data['id']}")
            
            await session.commit()
            await session.refresh(group)
            return group
            
    except Exception as e:
        logger.error(f"Error creating/updating group: {e}")
        return None


async def safe_execute_query(query: str, params: Optional[Dict] = None):
    """Execute query with comprehensive error handling."""
    try:
        return await db_manager.execute_query(query, params)
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return None


# Database migration functions
async def check_database_schema() -> bool:
    """Check if database schema is up to date."""
    try:
        async with get_session() as session:
            # Check if main tables exist
            tables_to_check = ['users', 'groups', 'api_keys']
            
            for table in tables_to_check:
                result = await session.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                )
                if not result.fetchone():
                    logger.warning(f"Table {table} not found")
                    return False
            
            logger.info("Database schema check passed")
            return True
            
    except Exception as e:
        logger.error(f"Database schema check failed: {e}")
        return False


async def migrate_database() -> bool:
    """Run database migrations."""
    try:
        # Create tables if they don't exist
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database migration completed")
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False