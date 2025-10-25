from rest_framework.permissions import BasePermission


# ----------------------------
# Dynamic Role Permission Factory
# ----------------------------
class RolePermissionFactory:
    """
    Usage:
        permission_classes = [IsAuthenticated, RolePermissionFactory(['ADMIN', 'DOC'])]
    """

    def __init__(self, allowed_roles=None):
        if allowed_roles is None:
            allowed_roles = []
        self.allowed_roles = allowed_roles

    def __call__(self):
        # Return a real permission class instance
        class RolePermission(BasePermission):
            def has_permission(inner_self, request, view):
                return (
                    request.user
                    and request.user.is_authenticated
                    and (request.user.role in self.allowed_roles or request.user.role == "ADMIN")
                )
        return RolePermission()
        

# ----------------------------
# Specific Role Permissions
# ----------------------------
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == "ADMIN" or request.user.is_superuser)


class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated  # ✅ FIXED!
            and hasattr(request.user, 'role')
            and request.user.role == "REC"
        )


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated  # ✅ FIXED!
            and hasattr(request.user, 'role')
            and request.user.role == "DOC"
        )


class IsLabTech(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated  # ✅ FIXED!
            and hasattr(request.user, 'role')
            and request.user.role == "LAB"
        )


class IsPharmacist(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated  # ✅ FIXED!
            and hasattr(request.user, 'role')
            and request.user.role == "PHARM"
        )
