# src/api/routes/folder_routes.py
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.core.scanner import scanner
from src.api.middleware.auth import security, require_permissions
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel

router = APIRouter(
   prefix="/folders",
   tags=["folders"],
   dependencies=[Depends(security)]
)

@router.get("/structure", summary="Get Folder Structure")
@require_permissions(["folders:read"])
async def get_folder_structure(
   root_path: str,
   current_request: Request,
   max_depth: Optional[int] = None,
   db: Session = Depends(get_db)
):
   try:
       if not Path(root_path).exists():
           raise HTTPException(status_code=404, detail="Path does not exist")

       result = scanner.get_folder_structure(
           root_path=root_path,
           max_depth=max_depth,
           simplified_system=True
       )

       if not result.get("success"):
           raise HTTPException(status_code=400, detail=result.get("error", "Failed to get folder structure"))

       # Transform the structure to match frontend expectations
       def transform_structure(node):
           transformed = {
               "name": node.get("name"),
               "path": node.get("path"),
               "type": "folder" if node.get("type") == "directory" else "file",
               "permissions": node.get("permissions", []),
               "children": []
           }
           
           # Recursively transform children
           if node.get("children"):
               transformed["children"] = [transform_structure(child) for child in node["children"]]
           
           # Add owner info if available
           if node.get("owner"):
               transformed["owner"] = node["owner"]
           
           # Add statistics if it's the root node
           if node.get("statistics"):
               transformed["statistics"] = node["statistics"]
           
           return transformed

       structure = transform_structure(result)

       return {
           "structure": structure,
           "metadata": {
               "root_path": root_path,
               "max_depth": max_depth,
               "total_folders": result.get("statistics", {}).get("total_folders", 0),
               "scanned_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}"
           }
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/permissions", summary="Get Folder Permissions")
@require_permissions(["folders:read"])
async def get_folder_permissions(
   path: str,
   current_request: Request,
   include_inherited: bool = True,
   simplified_system: bool = True,
   save_for_analysis: bool = False,
   db: Session = Depends(get_db)
):
   try:
       if not Path(path).exists():
           raise HTTPException(status_code=404, detail="Path does not exist")

       permissions = scanner.permission_scanner.get_folder_permissions(
           folder_path=path,
           include_inherited=include_inherited,
           simplified_system=simplified_system
       )

       # Save scan results if requested for health analysis
       if save_for_analysis and permissions.get("aces"):
           from src.db.models import ScanResult, AccessEntry
           from datetime import datetime
           import json
           
           # Create scan result without a job (for real-time analysis)
           scan_result = ScanResult(
               path=path,
               permissions=json.dumps(permissions),
               owner=json.dumps(permissions.get("owner", {})),
               scan_time=datetime.utcnow(),
               job_id=None,  # No associated job for real-time scans
               success=True
           )
           db.add(scan_result)
           db.flush()  # Get the ID
           
           # Store individual ACEs for detailed analysis
           for ace in permissions.get("aces", []):
               trustee = ace.get("trustee", {})
               access_entry = AccessEntry(
                   scan_result_id=scan_result.id,
                   trustee_name=trustee.get("name", "Unknown"),
                   trustee_domain=trustee.get("domain", ""),
                   trustee_sid=trustee.get("sid", ""),
                   access_type=ace.get("type", "Unknown"),
                   inherited=ace.get("is_inherited", False),
                   permissions=ace.get("permissions", {})
               )
               db.add(access_entry)
           
           db.commit()

       return {
           "path": path,
           "permissions": permissions,
           "metadata": {
               "include_inherited": include_inherited,
               "simplified_system": simplified_system,
               "scanned_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}",
               "scan_time": permissions.get("scan_time"),
               "saved_for_analysis": save_for_analysis
           }
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/access/{username}", summary="Get User Folder Access")
@require_permissions(["folders:read"])
async def get_user_folder_access(
   username: str,
   domain: str,
   current_request: Request,
   base_path: Optional[str] = None
):
   try:
       if base_path and not Path(base_path).exists():
           raise HTTPException(status_code=404, detail="Base path does not exist")

       access_info = scanner.get_user_access(
           username=username,
           domain=domain,
           base_path=base_path
       )

       return {
           "username": username,
           "domain": domain,
           "base_path": base_path,
           "access_info": access_info,
           "metadata": {
               "scanned_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}",
               "scan_time": access_info.get("scan_time")
           }
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate", summary="Validate Folder Accessibility")
@require_permissions(["folders:validate"])
async def validate_folder_access(
   path: str,
   current_request: Request,
   check_write: bool = False
):
   try:
       folder_path = Path(path)
       if not folder_path.exists():
           return {"valid": False, "reason": "Path does not exist"}

       try:
           # Test read access
           list(folder_path.iterdir())
           
           # Test write access if requested
           if check_write:
               test_file = folder_path / ".shareguard_write_test"
               try:
                   test_file.touch()
                   test_file.unlink()
               except:
                   return {
                       "valid": False,
                       "reason": "Write access denied",
                       "readable": True,
                       "writable": False
                   }

           return {
               "valid": True,
               "readable": True,
               "writable": check_write,
               "validated_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}"
           }

       except PermissionError:
           return {
               "valid": False,
               "reason": "Permission denied",
               "readable": False,
               "writable": False
           }

   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

# Pydantic models for ACL operations
class PermissionRequest(BaseModel):
    user_or_group: str
    domain: str
    permissions: List[str]  # ["read", "write", "execute", "delete", "modify", "full_control"]
    access_type: str = "allow"  # "allow" or "deny"

class PermissionResponse(BaseModel):
    success: bool
    message: str
    path: str
    user_or_group: str
    permissions: List[str]
    change_type: str  # "granted" or "revoked"

@router.put("/permissions", summary="Modify Folder Permissions")
@require_permissions(["folders:modify"])
async def modify_folder_permissions(
    path: str,
    permission_request: PermissionRequest,
    current_request: Request,
    db: Session = Depends(get_db)
):
    try:
        if not Path(path).exists():
            raise HTTPException(status_code=404, detail="Path does not exist")

        # Check if scanner has permission modification capability
        if not hasattr(scanner, 'permission_scanner') or not hasattr(scanner.permission_scanner, 'set_folder_permissions'):
            raise HTTPException(status_code=501, detail="ACL modification not implemented in scanner")

        # Record the change in database before making it
        from src.db.models.permissions import PermissionChange
        from datetime import datetime
        
        change_record = PermissionChange(
            folder_path=path,
            user_or_group=f"{permission_request.domain}\\{permission_request.user_or_group}",
            permission_type=",".join(permission_request.permissions),
            change_type="manual_grant",
            changed_by=f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}",
            change_time=datetime.utcnow()
        )
        db.add(change_record)
        db.commit()

        # Apply the permission change
        result = scanner.permission_scanner.set_folder_permissions(
            folder_path=path,
            user_or_group=f"{permission_request.domain}\\{permission_request.user_or_group}",
            permissions=permission_request.permissions,
            access_type=permission_request.access_type
        )

        if not result.get("success"):
            # Rollback the database change if permission setting failed
            db.delete(change_record)
            db.commit()
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to modify permissions"))

        return PermissionResponse(
            success=True,
            message=f"Permissions {'granted' if permission_request.access_type == 'allow' else 'denied'} successfully",
            path=path,
            user_or_group=f"{permission_request.domain}\\{permission_request.user_or_group}",
            permissions=permission_request.permissions,
            change_type="granted" if permission_request.access_type == "allow" else "denied"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/permissions", summary="Remove Folder Permissions")
@require_permissions(["folders:modify"])
async def remove_folder_permissions(
    path: str,
    user_or_group: str,
    domain: str,
    current_request: Request,
    db: Session = Depends(get_db)
):
    try:
        if not Path(path).exists():
            raise HTTPException(status_code=404, detail="Path does not exist")

        # Check if scanner has permission modification capability
        if not hasattr(scanner, 'permission_scanner') or not hasattr(scanner.permission_scanner, 'remove_folder_permissions'):
            raise HTTPException(status_code=501, detail="ACL modification not implemented in scanner")

        # Record the change in database before making it
        from src.db.models.permissions import PermissionChange
        from datetime import datetime
        
        change_record = PermissionChange(
            folder_path=path,
            user_or_group=f"{domain}\\{user_or_group}",
            permission_type="all",
            change_type="manual_revoke",
            changed_by=f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}",
            change_time=datetime.utcnow()
        )
        db.add(change_record)
        db.commit()

        # Remove the permissions
        result = scanner.permission_scanner.remove_folder_permissions(
            folder_path=path,
            user_or_group=f"{domain}\\{user_or_group}"
        )

        if not result.get("success"):
            # Rollback the database change if permission removal failed
            db.delete(change_record)
            db.commit()
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to remove permissions"))

        return PermissionResponse(
            success=True,
            message="Permissions removed successfully",
            path=path,
            user_or_group=f"{domain}\\{user_or_group}",
            permissions=["all"],
            change_type="revoked"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/group-members", summary="Get Group Members")
@require_permissions(["folders:read"])
async def get_group_members(
    group_name: str,
    domain: str,
    current_request: Request,
    include_nested: bool = True
):
    try:
        # Use the group resolver to get group members
        from src.scanner.group_resolver import GroupResolver
        from datetime import datetime
        
        group_resolver = GroupResolver()
        members_info = group_resolver.get_group_members(
            group_name=group_name,
            domain=domain,
            include_nested=include_nested
        )
        
        return {
            "group_info": members_info,
            "metadata": {
                "requested_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}",
                "include_nested": include_nested,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diagnose-sids", summary="Diagnose SID Resolution Issues")
@require_permissions(["folders:read"])
async def diagnose_sid_issues(
    path: str,
    current_request: Request
):
    try:
        from datetime import datetime
        
        if not Path(path).exists():
            raise HTTPException(status_code=404, detail="Path does not exist")

        # Use the scanner's diagnostic method
        diagnosis = scanner.permission_scanner.diagnose_sid_issues(path)
        
        return {
            "diagnosis": diagnosis,
            "metadata": {
                "diagnosed_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))