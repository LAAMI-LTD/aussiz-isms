from rest_framework import serializers
from .models import User, Role
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    roles = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                 'phone_number', 'employee_id', 'is_active', 'roles',
                 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                 'phone_number', 'employee_id', 'password', 'roles', 'is_active']
        read_only_fields = ['id']

    def create(self, validated_data):
        roles_data = validated_data.pop('roles', [])
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        if roles_data:
            user.roles.set(roles_data)

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users."""
    roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number',
                 'employee_id', 'is_active', 'roles']

    def update(self, instance, validated_data):
        roles_data = validated_data.pop('roles', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if roles_data is not None:
            instance.roles.set(roles_data)
        else:
            # Keep existing roles if not provided
            pass

        instance.save()
        return instance


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'user_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_count(self, obj):
        return obj.users.count()


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new roles."""

    class Meta:
        model = Role
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']