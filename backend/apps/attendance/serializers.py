from rest_framework import serializers
from .models import AttendanceSession, AttendanceStatus, AttendanceRecord
from apps.students.models import Student
from apps.courses.models import Class
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model (nested)."""
    class Meta:
        model = Student
        fields = ['id', 'student_id', 'first_name', 'last_name']
        read_only_fields = fields


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class model (nested)."""
    class Meta:
        model = Class
        fields = ['id', 'name', 'course']
        read_only_fields = fields


class AttendanceStatusSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceStatus model."""
    class Meta:
        model = AttendanceStatus
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceSessionSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceSession model."""
    class_instance = ClassSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceRecord model."""
    student = StudentSerializer(read_only=True)
    session = AttendanceSessionSerializer(read_only=True)
    status = AttendanceStatusSerializer(read_only=True)
    recorded_by = UserSerializer(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ['id', 'recorded_at', 'updated_at', 'recorded_by']

    def validate(self, attrs):
        """
        Validate that the student is enrolled in the class for this session.
        """
        session = attrs.get('session')
        student = attrs.get('student')

        if session and student:
            # Check if student is enrolled in the class
            is_enrolled = session.class_instance.enrollments.filter(
                student=student,
                is_active=True
            ).exists()

            if not is_enrolled:
                raise serializers.ValidationError({
                    'student': f'Student {student.get_full_name()} is not enrolled in class {session.class_instance.name}'
                })

        return attrs