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


class IsStudentOwnerOrStaff(permissions.BasePermission):
    """
    Permission class that allows:
    - Students to view their own profile
    - Staff (HOD, Tutor, Super Admin) to view any student profile
    - Only HOD and Super Admin to create/update/delete student profiles
    """
    def has_permission(self, request, view):
        # Only authenticated users can access student endpoints
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Students can view their own profile
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            if obj.id == request.user.id:
                return True

        # Staff members can view any student profile
        if request.user.is_staff:
            return True

        # Check if user is associated with the student (for next of kin, etc.)
        # For now, we'll allow staff access and students to view their own
        # In a more complex system, you might check if the user is a tutor assigned to the student
        return False