# src/db/models/changes.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class PermissionChange(Base):
    """Records of permission changes between scans."""
    __tablename__ = 'permission_changes'

    id = Column(Integer, primary_key=True)
    scan_job_id = Column(Integer, ForeignKey('scan_jobs.id'))
    access_entry_id = Column(Integer, ForeignKey('access_entries.id'))
    change_type = Column(String(50))
    previous_state = Column(JSON, nullable=True)
    current_state = Column(JSON)
    detected_time = Column(DateTime, default=datetime.utcnow)
    
    scan_job = relationship("ScanJob", back_populates="changes")
    access_entry = relationship("AccessEntry", back_populates="changes")
    alerts = relationship("Alert", back_populates="permission_change")

    __table_args__ = (
        Index('idx_permission_change_time', detected_time),
    )