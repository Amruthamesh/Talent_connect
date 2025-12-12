from fastapi import HTTPException, Depends, status
from app.models.user import User
from app.core.auth import get_current_active_user

# Permission definitions (matches frontend)
PERMISSIONS = {
    # Jobs Module
    "jobs.generate_jd": ["hr", "hiring_manager"],
    "jobs.jd.create": ["hr", "hiring_manager"],
    "jobs.jd.edit": ["hr", "hiring_manager"],
    "jobs.jd.view": ["hr", "recruiter", "hiring_manager"],
    "jobs.matcher.use": ["hr", "recruiter", "hiring_manager"],
    
    # Documents Module
    "docs.templates.all": ["hr"],
    "docs.templates.offer": ["hr", "recruiter"],
    "docs.templates.view": ["hiring_manager"],
    "docs.query.full": ["hr"],
    "docs.query.limited": ["recruiter"],
    
    # Interviews Module
    "interviews.dashboard": ["hr", "hiring_manager"],
    "interviews.schedule": ["hr", "hiring_manager"],
    "interviews.conduct": ["hr", "hiring_manager"],
    "interviews.view": ["recruiter"]
}


def has_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    allowed_roles = PERMISSIONS.get(permission, [])
    return user.role in allowed_roles


def require_permission(permission: str):
    """
    Dependency to enforce permission check
    Usage: @router.get("/endpoint", dependencies=[Depends(require_permission("jobs.jd.create"))])
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: {permission}"
            )
        return current_user
    return permission_checker


def require_roles(*allowed_roles: str):
    """
    Dependency to enforce role check
    Usage: @router.get("/endpoint", dependencies=[Depends(require_roles("hr", "hiring_manager"))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
