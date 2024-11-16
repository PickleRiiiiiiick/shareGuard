# src/db/models/__init__.py
from .scan import ScanTarget, ScanJob, ScanResult, AccessEntry
from .alerts import AlertConfiguration, Alert
from .changes import PermissionChange
from .cache import UserGroupMapping
from .enums import ScanScheduleType, AlertType, AlertSeverity

__all__ = [
    'ScanTarget',
    'ScanJob',
    'ScanResult',
    'AccessEntry',
    'AlertConfiguration',
    'Alert',
    'PermissionChange',
    'UserGroupMapping',
    'ScanScheduleType',
    'AlertType',
    'AlertSeverity'
]

# src/db/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Column, DateTime

Base = declarative_base()

class TimestampMixin:
    """Mixin for adding creation and update timestamps."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
