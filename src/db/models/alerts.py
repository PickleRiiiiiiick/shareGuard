# src/db/models/alerts.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, TimestampMixin
from .enums import AlertType, AlertSeverity

class AlertConfiguration(Base, TimestampMixin):
    """Alert configurations for permission changes."""
    __tablename__ = 'alert_configurations'

    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey('scan_targets.id'))
    name = Column(String(100))
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    conditions = Column(JSON)
    notifications = Column(JSON)
    is_active = Column(Boolean, default=True)

    target = relationship("ScanTarget", back_populates="alerts")
    triggered_alerts = relationship("Alert", back_populates="configuration")

class Alert(Base, TimestampMixin):
    """Record of triggered alerts."""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey('alert_configurations.id'))
    scan_job_id = Column(Integer, ForeignKey('scan_jobs.id'))
    permission_change_id = Column(Integer, ForeignKey('permission_changes.id'), nullable=True)
    severity = Column(String, nullable=False)
    message = Column(Text)
    details = Column(JSON)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)

    configuration = relationship("AlertConfiguration", back_populates="triggered_alerts")
    scan_job = relationship("ScanJob", back_populates="alerts")
    permission_change = relationship("PermissionChange", back_populates="alerts")