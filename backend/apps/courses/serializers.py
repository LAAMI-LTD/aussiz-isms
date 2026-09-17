from rest_framework import serializers
from .models import CourseCategory, Course, Class
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class CourseCategorySerializer(serializers.ModelSerializer):
    """Serializer for CourseCategory model."""
    class Meta:
        model = CourseCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""
    category = CourseCategorySerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'course_code', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate_course_code(self, value):
        """Ensure course code is unique."""
        queryset = Course.objects.filter(course_code=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A course with this course code already exists.")
        return value

    def validate(self, attrs):
        """Validate that minimum_students <= maximum_students."""
        minimum_students = attrs.get('minimum_students', getattr(self.instance, 'minimum_students', None))
        maximum_students = attrs.get('maximum_students', getattr(self.instance, 'maximum_students', None))

        if minimum_students is not None and maximum_students is not None:
            if minimum_students > maximum_students:
                raise serializers.ValidationError({
                    'minimum_students': 'Minimum students cannot be greater than maximum students.'
                })
        return attrs


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class model."""
    course = CourseSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate(self, attrs):
        """Validate that start_date <= end_date if end_date is provided."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({
                    'end_date': 'End date cannot be before start date.'
                })
        return attrs