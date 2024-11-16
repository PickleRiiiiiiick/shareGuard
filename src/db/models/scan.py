# src/db/models/scan.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, TimestampMixin
from .enums import ScanScheduleType

class ScanTarget(Base, TimestampMixin):
    """Represents a scan target configuration."""
    __tablename__ = 'scan_targets'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    path = Column(String(255), nullable=False)
    is_sensitive = Column(Boolean, default=False)
    scan_frequency = Column(String, nullable=False)
    max_depth = Column(Integer, nullable=True)
    exclude_patterns = Column(JSON, nullable=True)
    last_scan_time = Column(DateTime, nullable=True)

    scan_jobs = relationship("ScanJob", back_populates="target")
    alerts = relationship("AlertConfiguration", back_populates="target")

    __table_args__ = (
        Index('idx_scan_target_path', path),
    )

class ScanJob(Base, TimestampMixin):
    """Record of each scanning job."""
    __tablename__ = 'scan_jobs'

    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey('scan_targets.id'))
    scan_type = Column(String(50))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20))
    parameters = Column(JSON)
    error_message = Column(String(500), nullable=True)
    baseline_job_id = Column(Integer, ForeignKey('scan_jobs.id'), nullable=True)

    target = relationship("ScanTarget", back_populates="scan_jobs")
    results = relationship("ScanResult", back_populates="job")
    changes = relationship("PermissionChange", back_populates="scan_job")
    alerts = relationship("Alert", back_populates="scan_job")

class ScanResult(Base):
    """Detailed scan results."""
    __tablename__ = 'scan_results'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('scan_jobs.id'))
    path = Column(String(255))
    scan_time = Column(DateTime, default=datetime.utcnow)
    owner = Column(JSON)
    permissions = Column(JSON)
    success = Column(Boolean, default=True)
    error_message = Column(String(500), nullable=True)
    hash = Column(String(64), nullable=True)

    job = relationship("ScanJob", back_populates="results")
    access_entries = relationship("AccessEntry", back_populates="scan_result")

    __table_args__ = (
        Index('idx_scan_result_path', path),
        Index('idx_scan_result_hash', hash),
    )

class AccessEntry(Base):
    """Individual permission entries."""
    __tablename__ = 'access_entries'

    id = Column(Integer, primary_key=True)
    scan_result_id = Column(Integer, ForeignKey('scan_results.id'))
    trustee_name = Column(String(255))
    trustee_domain = Column(String(255))
    trustee_sid = Column(String(255))
    access_type = Column(String(50))
    inherited = Column(Boolean)
    permissions = Column(JSON)
    
    scan_result = relationship("ScanResult", back_populates="access_entries")
    changes = relationship("PermissionChange", back_populates="access_entry")

    __table_args__ = (
        Index('idx_access_entry_trustee', trustee_name, trustee_domain),
        Index('idx_access_entry_sid', trustee_sid),
    )