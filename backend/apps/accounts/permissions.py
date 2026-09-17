from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class that allows only super admins to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_super_admin
        )


class IsHODOrAbove(permissions.BasePermission):
    """
    Permission class that allows HOD and super admins to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_hod or request.user.is_super_admin)
        )


class IsTutorOrAbove(permissions.BasePermission):
    """
    Permission class that allows tutors, HOD, and super admins to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_tutor or request.user.is_hod or request.user.is_super_admin)
        )


class IsStaffOwnerOrSuperAdmin(permissions.BasePermission):
    """
    Permission class that allows staff to edit their own profile or super admins to edit any profile.
    """
    def has_object_permission(self, request, view, obj):
        # Super admins can do anything
        if request.user.is_super_admin:
            return True

        # Staff can edit their own profile
        return obj.id == request.user.id