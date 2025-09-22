from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    """
    Restrict access by user.role.
    """

    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role == "ADMIN" or request.user.role in self.allowed_roles
        )

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "ADMIN"

class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "REC"

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "DOC"

class IsLabTech(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "LAB"

class IsPharmacist(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "PHARM"
    
# class IsAdminOrReceptionist(BasePermission):
#     def has_permission(self, request, view):
#         return request.user and (request.user.role == "ADMIN" or request.user.role == "REC")