# src/db/models/folder_cache.py

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Index, Text
from sqlalchemy.sql import func
from datetime import datetime

from .base import Base

class FolderPermissionCache(Base):
    """Cache table for folder permissions to improve performance."""
    __tablename__ = "folder_permission_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    folder_path = Column(String(500), nullable=False, unique=True, index=True)
    permissions_data = Column(JSON, nullable=False)  # Stores the full permissions structure
    owner_info = Column(JSON, nullable=True)
    inheritance_enabled = Column(Boolean, default=True)
    last_scan_time = Column(DateTime, default=datetime.utcnow)
    last_modified_time = Column(DateTime, nullable=True)  # File system modification time
    is_stale = Column(Boolean, default=False)  # Mark as stale when changes detected
    scan_job_id = Column(Integer, nullable=True)  # Reference to the scan job that updated this
    checksum = Column(String(64), nullable=True)  # Optional checksum for validation
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create indexes for better query performance
    __table_args__ = (
        Index('idx_folder_path_stale', 'folder_path', 'is_stale'),
        Index('idx_last_scan_time', 'last_scan_time'),
        Index('idx_updated_at', 'updated_at'),
    )

class FolderStructureCache(Base):
    """Cache table for folder structure to improve tree loading."""
    __tablename__ = "folder_structure_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    root_path = Column(String(500), nullable=False, index=True)
    max_depth = Column(Integer, nullable=False)
    structure_data = Column(JSON, nullable=False)  # Stores the full folder tree structure
    total_folders = Column(Integer, default=0)
    scan_duration_ms = Column(Integer, nullable=True)
    last_scan_time = Column(DateTime, default=datetime.utcnow)
    is_stale = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create composite index for root_path and max_depth
    __table_args__ = (
        Index('idx_root_depth', 'root_path', 'max_depth'),
        Index('idx_structure_stale', 'root_path', 'is_stale'),
    )