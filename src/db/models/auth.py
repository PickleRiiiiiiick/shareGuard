# src/db/models/auth.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, TimestampMixin

class ServiceAccount(Base, TimestampMixin):
    """Service account for API authentication."""
    __tablename__ = 'service_accounts'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    description = Column(String(500))
    permissions = Column(JSON)  # List of permission strings
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)

    # Relationships
    sessions = relationship("AuthSession", back_populates="service_account")

    def __repr__(self):
        return f"<ServiceAccount {self.domain}\\{self.username}>"

class AuthSession(Base):
    """Authentication session tracking."""
    __tablename__ = 'auth_sessions'

    id = Column(Integer, primary_key=True)
    service_account_id = Column(Integer, ForeignKey('service_accounts.id'), nullable=False)
    token = Column(String(500), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    service_account = relationship("ServiceAccount", back_populates="sessions")

    def __repr__(self):
        return f"<AuthSession {self.id}>"