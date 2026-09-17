from rest_framework import serializers
from .models import Student, NextOfKin, StudentDocument
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class NextOfKinSerializer(serializers.ModelSerializer):
    """Serializer for NextOfKin model."""
    class Meta:
        model = NextOfKin
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentDocumentSerializer(serializers.ModelSerializer):
    """Serializer for StudentDocument model."""
    uploaded_by = UserSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)

    class Meta:
        model = StudentDocument
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at', 'file_size', 'uploaded_by', 'verified_by', 'verified_at']


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model."""
    next_of_kin = NextOfKinSerializer(read_only=True)
    documents = StudentDocumentSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['id', 'student_id', 'date_created', 'date_updated', 'created_by', 'updated_by']

    def validate_national_id_passport(self, value):
        """Ensure national ID/passport is unique."""
        queryset = Student.objects.filter(national_id_passport=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A student with this national ID/passport already exists.")
        return value

    def validate_phone_number(self, value):
        """Validate phone number format."""
        import re
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value