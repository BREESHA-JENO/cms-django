# receptionist_api_app/permissions.py
from rest_framework.permissions import BasePermission

def in_group(user, name):
    return user and user.is_authenticated and user.groups.filter(name=name).exists()

class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return in_group(request.user, 'Receptionist') or request.user.is_staff

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return in_group(request.user, 'Doctor') or request.user.is_staff

class IsAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or in_group(request.user, 'Admin'))
