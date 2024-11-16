# src/api/schemas.py
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class ScanRequest(BaseModel):
    path: str
    include_subfolders: bool = False
    max_depth: Optional[int] = None
    simplified_system: bool = True  # New field
    include_inherited: bool = True  # New field

class ScanResult(BaseModel):
    id: int
    job_id: int
    path: str
    scan_time: datetime
    owner: Optional[Dict]
    permissions: Dict
    success: bool
    error_message: Optional[str]

class ScanJob(BaseModel):
    id: int
    scan_type: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    target: str
    parameters: Dict
    error_message: Optional[str]

class AccessEntry(BaseModel):
    id: int
    scan_result_id: int
    trustee_name: str
    trustee_domain: str
    trustee_sid: str
    access_type: str
    inherited: bool
    permissions: Dict