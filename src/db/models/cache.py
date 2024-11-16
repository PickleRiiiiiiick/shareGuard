# src/db/models/cache.py
from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from .base import Base

class UserGroupMapping(Base):
    """Cache of user group memberships."""
    __tablename__ = 'user_group_mappings'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    user_domain = Column(String(255))
    user_sid = Column(String(255))
    group_name = Column(String(255))
    group_domain = Column(String(255))
    group_sid = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_lookup', user_name, user_domain),
        Index('idx_group_lookup', group_name, group_domain),
        Index('idx_sid_lookup', user_sid, group_sid),
    )