# src/api/routes/folder_routes.py
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.core.scanner import scanner
from src.api.middleware.auth import security, require_permissions
from typing import Optional
from pathlib import Path

router = APIRouter(
   prefix="/api/v1/folders",
   tags=["folders"],
   dependencies=[Depends(security)]
)

@router.get("/structure", summary="Get Folder Structure")
@require_permissions(["folders:read"])
async def get_folder_structure(
   root_path: str,
   max_depth: Optional[int] = None,
   db: Session = Depends(get_db),
   current_request: Request
):
   try:
       if not Path(root_path).exists():
           raise HTTPException(status_code=404, detail="Path does not exist")

       structure = scanner.get_folder_structure(
           root_path=root_path,
           max_depth=max_depth,
           simplified_system=True
       )

       return {
           "structure": structure,
           "metadata": {
               "root_path": root_path,
               "max_depth": max_depth,
               "total_folders": structure.get("statistics", {}).get("total_folders", 0),
               "scanned_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}"
           }
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/permissions", summary="Get Folder Permissions")
@require_permissions(["folders:read"])
async def get_folder_permissions(
   path: str,
   include_inherited: bool = True,
   simplified_system: bool = True,
   current_request: Request
):
   try:
       if not Path(path).exists():
           raise HTTPException(status_code=404, detail="Path does not exist")

       permissions = scanner.permission_scanner.get_folder_permissions(
           folder_path=path,
           include_inherited=include_inherited,
           simplified_system=simplified_system
       )

       return {
           "path": path,
           "permissions": permissions,
           "metadata": {
               "include_inherited": include_inherited,
               "simplified_system": simplified_system,
               "scanned_by": f"{current_request.state.service_account.domain}\\{current_request.state.service_account.username}",
               "scan_time": permissions.get("scan_time")
           }
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/access/{username}", summary="Get User Folder Access")
@require_permissions(["folders:read"])
async def get_user_folder_access(
   username: str,
   domain: str,
   base_path: Optional[str] = None,
   current_request: Request
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
   check_write: bool = False,
   current_request: Request
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