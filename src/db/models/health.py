# src/db/models/health.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class IssueSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(enum.Enum):
    BROKEN_INHERITANCE = "broken_inheritance"
    DIRECT_USER_ACE = "direct_user_ace"
    ORPHANED_SID = "orphaned_sid"
    EXCESSIVE_ACE_COUNT = "excessive_ace_count"
    CONFLICTING_DENY_ORDER = "conflicting_deny_order"
    OVER_PERMISSIVE_GROUPS = "over_permissive_groups"


class IssueStatus(enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class HealthScan(Base):
    """Health scan execution records."""
    __tablename__ = "health_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=func.now(), nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="running", nullable=False)  # running, completed, failed
    total_paths = Column(Integer, default=0)
    processed_paths = Column(Integer, default=0)
    issues_found = Column(Integer, default=0)
    overall_score = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    scan_parameters = Column(JSON, nullable=True)
    
    # Relationships
    issues = relationship("Issue", back_populates="health_scan", cascade="all, delete-orphan")


class Issue(Base):
    """Individual security issues detected during health scans."""
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    health_scan_id = Column(Integer, ForeignKey("health_scans.id"), nullable=False)
    
    # Issue identification
    issue_type = Column(Enum(IssueType), nullable=False, index=True)
    severity = Column(Enum(IssueSeverity), nullable=False, index=True)
    status = Column(Enum(IssueStatus), default=IssueStatus.ACTIVE, nullable=False, index=True)
    
    # Location and context
    path = Column(String(500), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Issue details
    affected_principals = Column(JSON, nullable=True)  # List of affected users/groups
    acl_details = Column(JSON, nullable=True)  # Detailed ACL information
    recommendations = Column(Text, nullable=True)
    
    # Risk assessment
    risk_score = Column(Float, nullable=False, default=0.0)
    impact_description = Column(Text, nullable=True)
    
    # Timestamps
    first_detected = Column(DateTime, default=func.now(), nullable=False)
    last_seen = Column(DateTime, default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Additional context data
    context_data = Column(JSON, nullable=True)  # Additional context data
    
    # Relationships
    health_scan = relationship("HealthScan", back_populates="issues")


class HealthMetrics(Base):
    """Aggregated health metrics over time."""
    __tablename__ = "health_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_date = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Overall metrics
    overall_score = Column(Float, nullable=False)
    total_issues = Column(Integer, default=0)
    
    # Issues by severity
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Issues by type
    broken_inheritance_count = Column(Integer, default=0)
    direct_user_ace_count = Column(Integer, default=0)
    orphaned_sid_count = Column(Integer, default=0)
    excessive_ace_count = Column(Integer, default=0)
    conflicting_deny_order_count = Column(Integer, default=0)
    over_permissive_groups_count = Column(Integer, default=0)
    
    # Scan coverage
    total_paths_scanned = Column(Integer, default=0)
    scan_duration_seconds = Column(Float, default=0.0)


class HealthScoreHistory(Base):
    """Historical health score tracking."""
    __tablename__ = "health_score_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    score = Column(Float, nullable=False)
    issue_count = Column(Integer, default=0)
    scan_id = Column(Integer, ForeignKey("health_scans.id"), nullable=True)
    
    # Breakdown by severity
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)