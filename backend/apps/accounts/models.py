from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class Role(models.Model):
    """Role model for RBAC."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser."""
    email = models.EmailField(blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roles = models.ManyToManyField(Role, related_name='users', blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    @property
    def is_super_admin(self):
        """Check if user has super admin role."""
        return self.roles.filter(name='Super Admin').exists()

    @property
    def is_hod(self):
        """Check if user has HOD role."""
        return self.roles.filter(name='HOD').exists()

    @property
    def is_tutor(self):
        """Check if user has tutor role."""
        return self.roles.filter(name='Tutor').exists()