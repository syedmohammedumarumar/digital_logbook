# attendance/permissions.py
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of an object or admin users"""
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.role == 'admin':
            return True
        
        # Users can only access their own objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user