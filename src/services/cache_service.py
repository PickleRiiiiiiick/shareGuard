# src/services/cache_service.py

import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path
import os

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.db.models.folder_cache import FolderPermissionCache, FolderStructureCache
from src.db.database import get_db
from src.utils.logger import setup_logger
from src.core.scanner import scanner

logger = setup_logger('cache_service')

class PermissionCacheService:
    """Service for managing folder permission caching."""
    
    def __init__(self):
        self.cache_ttl_hours = 24  # Cache validity period
        self.batch_size = 100  # Number of folders to process in batch
        
    def get_folder_permissions_cached(
        self, 
        db: Session,
        folder_path: str,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        Get folder permissions from cache or scan if needed.
        
        Args:
            db: Database session
            folder_path: Path to the folder
            force_refresh: Force a fresh scan even if cache exists
            
        Returns:
            Permissions data or None if not found
        """
        try:
            # Normalize path
            normalized_path = str(Path(folder_path).resolve())
            
            if not force_refresh:
                # Try to get from cache
                cache_entry = db.query(FolderPermissionCache).filter(
                    and_(
                        FolderPermissionCache.folder_path == normalized_path,
                        FolderPermissionCache.is_stale == False
                    )
                ).first()
                
                if cache_entry and self._is_cache_valid(cache_entry):
                    logger.debug(f"Cache hit for permissions: {normalized_path}")
                    return cache_entry.permissions_data
            
            # Cache miss or force refresh - scan the folder
            logger.info(f"Cache miss or refresh for permissions: {normalized_path}")
            permissions_data = scanner.permission_scanner.get_folder_permissions(
                normalized_path,
                simplified_system=True
            )
            
            # Update cache
            self._update_permission_cache(db, normalized_path, permissions_data)
            
            return permissions_data
            
        except Exception as e:
            logger.error(f"Error getting cached permissions for {folder_path}: {str(e)}")
            return None
    
    def get_folder_structure_cached(
        self,
        db: Session,
        root_path: str,
        max_depth: int,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        Get folder structure from cache or scan if needed.
        
        Args:
            db: Database session
            root_path: Root path for structure
            max_depth: Maximum depth to scan
            force_refresh: Force a fresh scan
            
        Returns:
            Folder structure data or None
        """
        try:
            normalized_path = str(Path(root_path).resolve())
            
            if not force_refresh:
                # Try to get from cache
                cache_entry = db.query(FolderStructureCache).filter(
                    and_(
                        FolderStructureCache.root_path == normalized_path,
                        FolderStructureCache.max_depth >= max_depth,
                        FolderStructureCache.is_stale == False
                    )
                ).first()
                
                if cache_entry and self._is_cache_valid_structure(cache_entry):
                    logger.debug(f"Cache hit for structure: {normalized_path}")
                    return cache_entry.structure_data
            
            # Cache miss - scan the structure
            logger.info(f"Cache miss or refresh for structure: {normalized_path}")
            start_time = datetime.utcnow()
            
            structure_data = scanner.get_folder_structure(
                normalized_path,
                max_depth=max_depth,
                simplified_system=True
            )
            
            scan_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Update cache
            self._update_structure_cache(
                db, 
                normalized_path, 
                max_depth, 
                structure_data,
                scan_duration_ms
            )
            
            return structure_data
            
        except Exception as e:
            logger.error(f"Error getting cached structure for {root_path}: {str(e)}")
            return None
    
    def mark_path_stale(self, db: Session, path: str) -> None:
        """Mark a path and all its children as stale in the cache."""
        try:
            normalized_path = str(Path(path).resolve())
            
            # Mark exact path as stale
            db.query(FolderPermissionCache).filter(
                FolderPermissionCache.folder_path == normalized_path
            ).update({"is_stale": True})
            
            # Mark all child paths as stale
            db.query(FolderPermissionCache).filter(
                FolderPermissionCache.folder_path.like(f"{normalized_path}%")
            ).update({"is_stale": True})
            
            # Mark structure caches as stale if they contain this path
            db.query(FolderStructureCache).filter(
                or_(
                    FolderStructureCache.root_path == normalized_path,
                    FolderStructureCache.root_path.like(f"{normalized_path}%"),
                    normalized_path.like(FolderStructureCache.root_path + "%")
                )
            ).update({"is_stale": True})
            
            db.commit()
            logger.info(f"Marked cache stale for path: {normalized_path}")
            
        except Exception as e:
            logger.error(f"Error marking path stale: {str(e)}")
            db.rollback()
    
    def cleanup_stale_cache(self, db: Session, older_than_hours: int = 48) -> int:
        """Remove stale cache entries older than specified hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            # Delete old permission cache entries
            deleted_perms = db.query(FolderPermissionCache).filter(
                or_(
                    and_(
                        FolderPermissionCache.is_stale == True,
                        FolderPermissionCache.updated_at < cutoff_time
                    ),
                    FolderPermissionCache.last_scan_time < cutoff_time
                )
            ).delete()
            
            # Delete old structure cache entries
            deleted_structs = db.query(FolderStructureCache).filter(
                or_(
                    and_(
                        FolderStructureCache.is_stale == True,
                        FolderStructureCache.updated_at < cutoff_time
                    ),
                    FolderStructureCache.last_scan_time < cutoff_time
                )
            ).delete()
            
            db.commit()
            
            total_deleted = deleted_perms + deleted_structs
            logger.info(f"Cleaned up {total_deleted} stale cache entries")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")
            db.rollback()
            return 0
    
    def _is_cache_valid(self, cache_entry: FolderPermissionCache) -> bool:
        """Check if cache entry is still valid."""
        if cache_entry.is_stale:
            return False
            
        # Check age
        age = datetime.utcnow() - cache_entry.last_scan_time
        if age.total_seconds() > self.cache_ttl_hours * 3600:
            return False
            
        # Optionally check file system modification time
        try:
            folder_stat = os.stat(cache_entry.folder_path)
            folder_mtime = datetime.fromtimestamp(folder_stat.st_mtime)
            
            if cache_entry.last_modified_time and folder_mtime > cache_entry.last_modified_time:
                return False
                
        except Exception:
            # If we can't check, assume cache is valid
            pass
            
        return True
    
    def _is_cache_valid_structure(self, cache_entry: FolderStructureCache) -> bool:
        """Check if structure cache entry is still valid."""
        if cache_entry.is_stale:
            return False
            
        # Check age
        age = datetime.utcnow() - cache_entry.last_scan_time
        if age.total_seconds() > self.cache_ttl_hours * 3600:
            return False
            
        return True
    
    def _update_permission_cache(
        self, 
        db: Session, 
        folder_path: str, 
        permissions_data: Dict
    ) -> None:
        """Update or create cache entry for folder permissions."""
        try:
            # Get file modification time
            folder_mtime = None
            try:
                folder_stat = os.stat(folder_path)
                folder_mtime = datetime.fromtimestamp(folder_stat.st_mtime)
            except Exception:
                pass
            
            # Calculate checksum of permissions data
            checksum = hashlib.sha256(
                json.dumps(permissions_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Check if entry exists
            cache_entry = db.query(FolderPermissionCache).filter(
                FolderPermissionCache.folder_path == folder_path
            ).first()
            
            if cache_entry:
                # Update existing entry
                cache_entry.permissions_data = permissions_data
                cache_entry.last_scan_time = datetime.utcnow()
                cache_entry.last_modified_time = folder_mtime
                cache_entry.is_stale = False
                cache_entry.checksum = checksum
                cache_entry.updated_at = datetime.utcnow()
                
                # Extract owner info if available
                if 'owner' in permissions_data:
                    cache_entry.owner_info = permissions_data['owner']
                    
                if 'inheritance_enabled' in permissions_data:
                    cache_entry.inheritance_enabled = permissions_data['inheritance_enabled']
            else:
                # Create new entry
                cache_entry = FolderPermissionCache(
                    folder_path=folder_path,
                    permissions_data=permissions_data,
                    last_scan_time=datetime.utcnow(),
                    last_modified_time=folder_mtime,
                    is_stale=False,
                    checksum=checksum,
                    owner_info=permissions_data.get('owner'),
                    inheritance_enabled=permissions_data.get('inheritance_enabled', True)
                )
                db.add(cache_entry)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating permission cache: {str(e)}")
            db.rollback()
    
    def _update_structure_cache(
        self,
        db: Session,
        root_path: str,
        max_depth: int,
        structure_data: Dict,
        scan_duration_ms: int
    ) -> None:
        """Update or create cache entry for folder structure."""
        try:
            # Check if entry exists
            cache_entry = db.query(FolderStructureCache).filter(
                and_(
                    FolderStructureCache.root_path == root_path,
                    FolderStructureCache.max_depth == max_depth
                )
            ).first()
            
            total_folders = structure_data.get('statistics', {}).get('total_folders', 0)
            
            if cache_entry:
                # Update existing entry
                cache_entry.structure_data = structure_data
                cache_entry.last_scan_time = datetime.utcnow()
                cache_entry.is_stale = False
                cache_entry.total_folders = total_folders
                cache_entry.scan_duration_ms = scan_duration_ms
                cache_entry.updated_at = datetime.utcnow()
            else:
                # Create new entry
                cache_entry = FolderStructureCache(
                    root_path=root_path,
                    max_depth=max_depth,
                    structure_data=structure_data,
                    last_scan_time=datetime.utcnow(),
                    is_stale=False,
                    total_folders=total_folders,
                    scan_duration_ms=scan_duration_ms
                )
                db.add(cache_entry)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating structure cache: {str(e)}")
            db.rollback()

# Global cache service instance
cache_service = PermissionCacheService()