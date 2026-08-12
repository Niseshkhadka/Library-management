from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SUPERADMIN'


class IsLibrarian(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'LIBRARIAN'


class IsMember(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'MEMBER'


class IsLibrarianOrSuperAdmin(BasePermission):
    """Useful for actions both roles should be able to do, e.g. managing books"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['LIBRARIAN', 'SUPERADMIN']