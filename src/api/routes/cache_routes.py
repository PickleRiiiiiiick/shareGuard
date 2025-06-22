# src/api/routes/cache_routes.py
from fastapi import APIRouter, Depends, Request
from src.core.scanner import scanner
from src.api.middleware.auth import security, require_permissions

router = APIRouter(
   prefix="/cache",
   tags=["cache"],
   dependencies=[Depends(security)]
)

@router.post("/clear", summary="Clear Cache")
@require_permissions(["cache:clear"])
async def clear_all_cache(current_request: Request):
   """Clear all system caches including group resolver and scan results."""
   service_account = current_request.state.service_account
   scanner.group_resolver.clear_cache()
   return {
       "message": "All caches cleared successfully",
       "cleared_by": f"{service_account.domain}\\{service_account.username}"
   }

@router.get("/status", summary="Get Cache Status")
@require_permissions(["cache:read"])
async def get_cache_status(current_request: Request):
   """Get current cache statistics."""
   cache = scanner.group_resolver._cache
   return {
       "groups_cached": len(cache.get('groups', {})),
       "users_cached": len(cache.get('users', {})),
       "paths_cached": len(cache.get('paths', {})),
       "memberships_cached": len(cache.get('memberships', {})),
       "group_members_cached": len(cache.get('group_members', {})),
       "last_cleared_by": cache.get('last_cleared_by', None),
       "last_cleared_at": cache.get('last_cleared_at', None)
   }

@router.post("/groups/clear", summary="Clear Groups Cache")
@require_permissions(["cache:clear"])
async def clear_groups_cache(current_request: Request):
   """Clear only the groups resolver cache."""
   service_account = current_request.state.service_account
   scanner.group_resolver.clear_cache('groups')
   return {
       "message": "Groups cache cleared successfully",
       "cleared_by": f"{service_account.domain}\\{service_account.username}"
   }

@router.post("/paths/clear", summary="Clear Paths Cache")
@require_permissions(["cache:clear"])
async def clear_paths_cache(current_request: Request):
   """Clear only the paths cache."""
   service_account = current_request.state.service_account
   scanner.group_resolver.clear_cache('paths')
   return {
       "message": "Paths cache cleared successfully",
       "cleared_by": f"{service_account.domain}\\{service_account.username}"
   }