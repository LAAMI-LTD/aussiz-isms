from rest_framework import serializers
from .models import CourseCategory, Course, Class, Enrollment
from apps.accounts.models import User
from apps.students.models import Student


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
    category_id = serializers.UUIDField(write_only=True)
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
    course_id = serializers.UUIDField(write_only=True)
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


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model."""
    student = serializers.StringRelatedField(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    class_instance = serializers.StringRelatedField(read_only=True)
    class_instance_id = serializers.UUIDField(write_only=True)
    course_details = serializers.SerializerMethodField(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['id', 'enrollment_date', 'created_at', 'updated_at', 'created_by', 'updated_by', 'student', 'class_instance']

    def get_course_details(self, obj):
        """Return course details for the enrolled class."""
        return {
            'course_code': obj.class_instance.course.course_code,
            'course_name': obj.class_instance.course.name,
            'course_type': obj.class_instance.course.course_type
        }

    def validate(self, attrs):
        """Validate enrollment data."""
        student_id = attrs.get('student_id')
        class_instance_id = attrs.get('class_instance_id')

        # Check if student is already enrolled in this class
        if student_id and class_instance_id:
            existing_enrollment = Enrollment.objects.filter(
                student_id=student_id,
                class_instance_id=class_instance_id,
                is_active=True
            ).exclude(
                pk=getattr(self.instance, 'pk', None)
            ).first()

            if existing_enrollment:
                raise serializers.ValidationError({
                    'non_field_errors': 'Student is already enrolled in this class.'
                })

        return attrs