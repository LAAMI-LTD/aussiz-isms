from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile, name='profile'),

    # User management endpoints (Super Admin only)
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),

    # Role management endpoints (Super Admin only)
    path('roles/', views.RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role-detail'),

    # Role assignment endpoints (Super Admin only)
    path('users/<int:user_id>/assign-role/', views.assign_role_to_user, name='assign-role-to-user'),
    path('users/<int:user_id>/remove-role/', views.remove_role_from_user, name='remove-role-from-user'),

    # Dashboard stats
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
]