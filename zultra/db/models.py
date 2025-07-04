"""
SQLAlchemy database models for Zultra Telegram Bot.
Contains all database tables and relationships.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, Boolean, 
    Float, ForeignKey, Index, JSON, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model for storing Telegram user information."""
    
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(32), nullable=True, index=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=True)
    language_code = Column(String(8), nullable=True)
    is_bot = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Bot-specific fields
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    banned_at = Column(DateTime(timezone=True), nullable=True)
    banned_by = Column(BigInteger, nullable=True)
    
    # Statistics
    message_count = Column(Integer, default=0)
    ai_requests = Column(Integer, default=0)
    last_seen = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    groups = relationship("UserGroup", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    usage_stats = relationship("Usage", back_populates="user")
    warnings = relationship("Warning", back_populates="user")
    afk_status = relationship("AFKUser", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Group(Base):
    """Group/Chat model for storing Telegram group information."""
    
    __tablename__ = "groups"
    
    id = Column(BigInteger, primary_key=True)  # Telegram chat ID
    title = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # private, group, supergroup, channel
    username = Column(String(32), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Group settings
    language = Column(String(8), default="en")
    timezone = Column(String(32), default="UTC")
    
    # Feature toggles
    ai_enabled = Column(Boolean, default=True)
    fun_commands_enabled = Column(Boolean, default=True)
    admin_commands_enabled = Column(Boolean, default=True)
    anti_spam_enabled = Column(Boolean, default=True)
    captcha_enabled = Column(Boolean, default=False)
    raid_mode = Column(Boolean, default=False)
    
    # Moderation settings
    max_warnings = Column(Integer, default=3)
    auto_delete_commands = Column(Boolean, default=False)
    welcome_message = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    
    # Statistics
    member_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    ai_requests = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    members = relationship("UserGroup", back_populates="group")
    api_keys = relationship("APIKey", back_populates="group")
    usage_stats = relationship("Usage", back_populates="group")
    warnings = relationship("Warning", back_populates="group")
    banned_users = relationship("BannedUser", back_populates="group")
    
    def __repr__(self):
        return f"<Group(id={self.id}, title={self.title})>"


class UserGroup(Base):
    """Association table for User-Group relationships with roles."""
    
    __tablename__ = "user_groups"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    group_id = Column(BigInteger, ForeignKey("groups.id"), primary_key=True)
    role = Column(String(20), default="member")  # owner, admin, member
    joined_at = Column(DateTime(timezone=True), default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")
    
    def __repr__(self):
        return f"<UserGroup(user_id={self.user_id}, group_id={self.group_id}, role={self.role})>"


class APIKey(Base):
    """Encrypted API keys for AI providers per user/group."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=True)
    provider = Column(String(20), nullable=False)  # openai, gemini
    encrypted_key = Column(LargeBinary, nullable=False)
    key_name = Column(String(50), nullable=True)  # User-defined name
    is_active = Column(Boolean, default=True)
    
    # Usage limits
    daily_limit = Column(Integer, nullable=True)
    monthly_limit = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    group = relationship("Group", back_populates="api_keys")
    usage_stats = relationship("Usage", back_populates="api_key")
    
    __table_args__ = (
        Index("idx_api_keys_user_provider", "user_id", "provider"),
        Index("idx_api_keys_group_provider", "group_id", "provider"),
    )
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, provider={self.provider}, user_id={self.user_id})>"


class Usage(Base):
    """Usage tracking for AI requests and tokens."""
    
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    
    provider = Column(String(20), nullable=False)
    model = Column(String(50), nullable=True)
    request_type = Column(String(20), nullable=False)  # completion, image, etc.
    
    # Usage metrics
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    request_time = Column(Float, default=0.0)  # Response time in seconds
    
    # Request details
    prompt_length = Column(Integer, default=0)
    response_length = Column(Integer, default=0)
    status = Column(String(20), default="success")  # success, error, rate_limited
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_stats")
    group = relationship("Group", back_populates="usage_stats")
    api_key = relationship("APIKey", back_populates="usage_stats")
    
    __table_args__ = (
        Index("idx_usage_user_date", "user_id", "created_at"),
        Index("idx_usage_group_date", "group_id", "created_at"),
        Index("idx_usage_provider_date", "provider", "created_at"),
    )
    
    def __repr__(self):
        return f"<Usage(id={self.id}, provider={self.provider}, tokens={self.tokens_used})>"


class AFKUser(Base):
    """AFK (Away From Keyboard) status for users."""
    
    __tablename__ = "afk_users"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    group_id = Column(BigInteger, ForeignKey("groups.id"), primary_key=True)
    reason = Column(Text, nullable=True)
    afk_since = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="afk_status")
    
    def __repr__(self):
        return f"<AFKUser(user_id={self.user_id}, group_id={self.group_id})>"


class Warning(Base):
    """User warnings in groups."""
    
    __tablename__ = "warnings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False)
    warned_by = Column(BigInteger, nullable=False)  # Admin who issued warning
    reason = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="warnings")
    group = relationship("Group", back_populates="warnings")
    
    __table_args__ = (
        Index("idx_warnings_user_group", "user_id", "group_id"),
    )
    
    def __repr__(self):
        return f"<Warning(id={self.id}, user_id={self.user_id}, group_id={self.group_id})>"


class BannedUser(Base):
    """Banned users in groups."""
    
    __tablename__ = "banned_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    group_id = Column(BigInteger, ForeignKey("groups.id"), nullable=False)
    banned_by = Column(BigInteger, nullable=False)  # Admin who banned
    reason = Column(Text, nullable=False)
    ban_type = Column(String(20), default="permanent")  # permanent, temporary
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="banned_users")
    
    __table_args__ = (
        Index("idx_banned_users_user_group", "user_id", "group_id"),
    )
    
    def __repr__(self):
        return f"<BannedUser(user_id={self.user_id}, group_id={self.group_id})>"


class RateLimitEntry(Base):
    """Rate limiting entries for users."""
    
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    action_type = Column(String(50), nullable=False)  # message, ai_request, etc.
    count = Column(Integer, default=1)
    window_start = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        Index("idx_rate_limits_user_action", "user_id", "action_type"),
        Index("idx_rate_limits_expires", "expires_at"),
    )
    
    def __repr__(self):
        return f"<RateLimitEntry(user_id={self.user_id}, action={self.action_type}, count={self.count})>"


class BotConfig(Base):
    """Bot configuration and settings."""
    
    __tablename__ = "bot_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BotConfig(key={self.key})>"