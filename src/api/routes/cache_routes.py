# src/api/routes/cache_routes.py
from fastapi import APIRouter
from core.scanner import scanner

router = APIRouter(
    prefix="/api/v1/cache",
    tags=["cache"],
    responses={404: {"description": "Not found"}},
)

@router.post("/clear")
async def clear_all_cache():
    """Clear all system caches including group resolver and scan results."""
    scanner.group_resolver.clear_cache()
    return {"message": "All caches cleared successfully"}

@router.get("/status")
async def get_cache_status():
    """Get current cache statistics."""
    cache = scanner.group_resolver._cache
    return {
        "groups_cached": len(cache['groups']),
        "users_cached": len(cache['users']),
        "paths_cached": len(cache['paths']),
        "memberships_cached": len(cache['memberships']),
        "group_members_cached": len(cache['group_members'])
    }