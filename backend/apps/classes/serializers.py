from rest_framework import serializers
from apps.courses.models import Class  # Class model is defined in courses app
from apps.courses.models import Course
from apps.students.models import Student
from apps.accounts.models import User
from apps.courses.serializers import CourseSerializer
from apps.students.serializers import StudentSerializer
from apps.accounts.serializers import UserSerializer


class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer for Class model.
    """
    course = CourseSerializer(read_only=True)
    course_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Computed properties
    student_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Class
        fields = [
            'id', 'course', 'course_id', 'name', 'start_date', 'end_date',
            'status', 'is_active', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'student_count', 'is_full',
            'available_spots', 'duration_days'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_course_id(self, value):
        """
        Validate that the course exists.
        """
        try:
            Course.objects.get(id=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist.")
        return value

    def create(self, validated_data):
        """
        Create and return a new class instance.
        """
        course_id = validated_data.pop('course_id')
        course = Course.objects.get(id=course_id)
        validated_data['course'] = course
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing class instance.
        """
        course_id = validated_data.pop('course_id', None)
        if course_id:
            course = Course.objects.get(id=course_id)
            validated_data['course'] = course
        return super().update(instance, validated_data)


class ClassDetailSerializer(ClassSerializer):
    """
    Detailed serializer for Class model with related data.
    """
    enrollments = serializers.SerializerMethodField()

    class Meta(ClassSerializer.Meta):
        fields = ClassSerializer.Meta.fields + ['enrollments']

    def get_enrollments(self, obj):
        """
        Get enrollments for this class.
        """
        from apps.courses.serializers import EnrollmentSerializer
        enrollments = obj.enrollments.filter(is_active=True)
        return EnrollmentSerializer(enrollments, many=True).data


# Additional serializers for related functionality
class ClassScheduleSerializer(serializers.Serializer):
    """
    Serializer for class schedule information.
    """
    session_date = serializers.DateField()
    session_number = serializers.IntegerField()
    topic = serializers.CharField(max_length=200, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)