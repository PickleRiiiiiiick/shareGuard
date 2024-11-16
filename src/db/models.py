# src/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ScanTarget(Base):
    """Pre-approved scan targets."""
    __tablename__ = 'scan_targets'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)  # Friendly name
    path = Column(String(255), unique=True)  # Actual file system path
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))  # User who added the target
    status = Column(String(50), default='active')  # active, disabled, etc.
    metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Optional fields for organization
    department = Column(String(255), nullable=True)
    owner = Column(String(255), nullable=True)
    sensitivity_level = Column(String(50), nullable=True)  # public, confidential, etc.
    scan_frequency = Column(String(50), nullable=True)  # daily, weekly, monthly
    
    # Relationships
    scan_jobs = relationship("ScanJob", back_populates="target")

class ScanJob(Base):
    """Record of each scanning job."""
    __tablename__ = 'scan_jobs'

    id = Column(Integer, primary_key=True)
    scan_type = Column(String(50))  # 'path', 'user', or 'structure'
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20))  # 'running', 'completed', 'failed'
    target_id = Column(Integer, ForeignKey('scan_targets.id'))
    parameters = Column(JSON)  # scan parameters
    error_message = Column(String(500), nullable=True)
    
    # Relationships
    target = relationship("ScanTarget", back_populates="scan_jobs")
    results = relationship("ScanResult", back_populates="job")

class ScanResult(Base):
    """Detailed scan results."""
    __tablename__ = 'scan_results'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('scan_jobs.id'))
    path = Column(String(255))
    scan_time = Column(DateTime, default=datetime.utcnow)
    owner = Column(JSON)  # Owner information
    permissions = Column(JSON)  # Full permission data
    success = Column(Boolean, default=True)
    error_message = Column(String(500), nullable=True)

    # Relationships
    job = relationship("ScanJob", back_populates="results")
    access_entries = relationship("AccessEntry", back_populates="scan_result")

class AccessEntry(Base):
    """Individual permission entries."""
    __tablename__ = 'access_entries'

    id = Column(Integer, primary_key=True)
    scan_result_id = Column(Integer, ForeignKey('scan_results.id'))
    trustee_name = Column(String(255))
    trustee_domain = Column(String(255))
    trustee_sid = Column(String(255))
    access_type = Column(String(50))  # 'Allow' or 'Deny'
    inherited = Column(Boolean)
    permissions = Column(JSON)  # Categorized permissions

    scan_result = relationship("ScanResult", back_populates="access_entries")

class UserGroupMapping(Base):
    """Cache of user group memberships."""
    __tablename__ = 'user_group_mappings'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    user_domain = Column(String(255))
    group_name = Column(String(255))
    group_domain = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)