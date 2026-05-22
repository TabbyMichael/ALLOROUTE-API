from rest_framework import permissions
from apps.common.roles import UserRole


class BaseRolePermission(permissions.BasePermission):
    """
    Base class for role-based permissions.
    """
    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Priority 1: Role from JWT token (stateless optimization)
        role = getattr(request.user, "token_role", None)
        
        # Priority 2: Role from DB profile (fallback)
        if not role:
            profile = getattr(request.user, "profile", None)
            if profile:
                role = profile.role
        
        if not role:
            return False
            
        return role in [role.value for role in self.allowed_roles]


class IsAdminUser(BaseRolePermission):
    """
    Allows access only to admin users.
    """
    allowed_roles = [UserRole.ADMIN]


class IsPremiumUser(BaseRolePermission):
    """
    Allows access only to premium (and admin) users.
    """
    allowed_roles = [UserRole.ADMIN, UserRole.PREMIUM]


class IsBasicUser(BaseRolePermission):
    """
    Allows access to all registered users (Basic, Premium, Admin).
    """
    allowed_roles = [UserRole.ADMIN, UserRole.PREMIUM, UserRole.BASIC]
