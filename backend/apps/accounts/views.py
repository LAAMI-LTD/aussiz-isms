from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import User, Role
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    RoleSerializer, RoleCreateSerializer
)
from .permissions import (
    IsSuperAdmin, IsHODOrAbove, IsStaffOwnerOrSuperAdmin
)
import logging

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """Generate JWT tokens for user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint for obtaining JWT tokens.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'User account is disabled'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    tokens = get_tokens_for_user(user)
    logger.info(f"User {user.username} logged in successfully")

    return Response({
        'tokens': tokens,
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint to blacklist refresh token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User {request.user.username} logged out successfully")
            return Response({'message': 'Successfully logged out'})
        else:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return Response(
            {'error': 'Error during logout'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user's profile information.
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_super_admin': user.is_super_admin,
        'is_hod': user.is_hod,
        'is_tutor': user.is_tutor,
        'roles': [role.name for role in user.roles.all()]
    })


# User Management Views
class UserListCreateView(generics.ListCreateAPIView):
    """
    List all users or create a new user.
    Only accessible by super admins.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined', 'last_login']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user instance.
    Only accessible by super admins, or users can edit their own profile.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsStaffOwnerOrSuperAdmin]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        """
        Instead of deleting, deactivate the user.
        """
        instance.is_active = False
        instance.save()
        logger.info(f"User {instance.username} deactivated by {self.request.user.username}")


# Role Management Views
class RoleListCreateView(generics.ListCreateAPIView):
    """
    List all roles or create a new role.
    Only accessible by super admins.
    """
    queryset = Role.objects.all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoleCreateSerializer
        return RoleSerializer


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a role instance.
    Only accessible by super admins.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsSuperAdmin]

    def perform_destroy(self, instance):
        """
        Instead of deleting, we could check if role is assigned to users.
        For now, we'll allow deletion but log it.
        """
        user_count = instance.users.count()
        if user_count > 0:
            logger.warning(
                f"Role {instance.name} is assigned to {user_count} users. "
                f"Deletion may cause permission issues."
            )
        instance.delete()
        logger.info(f"Role {instance.name} deleted by {self.request.user.username}")


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def assign_role_to_user(request, user_id):
    """
    Assign a role to a user.
    Only accessible by super admins.
    """
    try:
        user = User.objects.get(id=user_id)
        role_id = request.data.get('role_id')

        if not role_id:
            return Response(
                {'error': 'role_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        role = Role.objects.get(id=role_id)
        user.roles.add(role)

        logger.info(
            f"Role {role.name} assigned to user {user.username} "
            f"by {request.user.username}"
        )

        return Response({
            'message': f'Role {role.name} assigned to user {user.username}'
        })

    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Role.DoesNotExist:
        return Response(
            {'error': 'Role not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error assigning role: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def remove_role_from_user(request, user_id):
    """
    Remove a role from a user.
    Only accessible by super admins.
    """
    try:
        user = User.objects.get(id=user_id)
        role_id = request.data.get('role_id')

        if not role_id:
            return Response(
                {'error': 'role_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        role = Role.objects.get(id=role_id)
        user.roles.remove(role)

        logger.info(
            f"Role {role.name} removed from user {user.username} "
            f"by {request.user.username}"
        )

        return Response({
            'message': f'Role {role.name} removed from user {user.username}'
        })

    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Role.DoesNotExist:
        return Response(
            {'error': 'Role not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error removing role: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics.
    Accessible by all authenticated users, but data shown depends on role.
    """
    user = request.user

    # Base stats that everyone can see
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }

    # Additional stats for HOD and above
    if user.is_hod or user.is_super_admin:
        stats.update({
            'total_students': 0,  # Will be implemented in students app
            'active_students': 0,  # Will be implemented in students app
            'total_courses': 0,    # Will be implemented in courses app
            'active_courses': 0,   # Will be implemented in courses app
        })

    # Full stats for super admins
    if user.is_super_admin:
        stats.update({
            'total_roles': Role.objects.count(),
            'users_by_role': {},
        })

        # Get user count by role
        for role in Role.objects.all():
            stats['users_by_role'][role.name] = role.users.count()

    return Response(stats)