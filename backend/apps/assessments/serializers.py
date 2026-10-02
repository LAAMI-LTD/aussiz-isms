from rest_framework import serializers
from .models import Assessment, PracticeTest, MockTest, TestScore, AssessmentAttempt, ComponentScore, TargetBand
from apps.students.models import Student
from apps.courses.models import Course, Class
from apps.accounts.models import User
from apps.courses.serializers import CourseSerializer
from apps.students.serializers import StudentSerializer
from apps.accounts.serializers import UserSerializer


class AssessmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Assessment model.
    """
    course = CourseSerializer(read_only=True)
    course_id = serializers.UUIDField(write_only=True)
    class_instance = serializers.StringRelatedField(read_only=True)
    class_instance_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Computed properties
    is_passing_score = serializers.SerializerMethodField()
    test_score_components = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id', 'name', 'assessment_type', 'description',
            'course', 'course_id', 'class_instance', 'class_instance_id',
            'scheduled_date', 'start_time', 'end_time', 'duration_minutes',
            'instructions', 'materials_required',
            'total_score', 'passing_score',
            'is_active', 'is_available',
            'created_by', 'updated_by', 'created_at', 'updated_at',
            'is_passing_score', 'test_score_components'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def get_is_passing_score(self, obj):
        """Get passing score percentage."""
        return obj.is_passing_score

    def get_test_score_components(self, obj):
        """Get test score components for this assessment."""
        from .serializers import TestScoreSerializer
        components = obj.test_scores.all()
        return TestScoreSerializer(components, many=True).data

    def validate(self, attrs):
        """
        Validate the assessment data.
        """
        # Ensure course exists
        course_id = attrs.get('course_id')
        if course_id:
            try:
                Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise serializers.ValidationError({"course_id": "Course does not exist."})

        # Ensure class_instance exists if provided
        class_instance_id = attrs.get('class_instance_id')
        if class_instance_id:
            try:
                Class.objects.get(id=class_instance_id)
            except Class.DoesNotExist:
                raise serializers.ValidationError({"class_instance_id": "Class does not exist."})

        # Validate timing consistency
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        duration_minutes = attrs.get('duration_minutes')

        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError({"end_time": "End time must be after start time."})

            if duration_minutes is not None:
                from datetime import datetime, date
                today = date.today()
                start_dt = datetime.combine(today, start_time)
                end_dt = datetime.combine(today, end_time)
                calculated_duration = int((end_dt - start_dt).total_seconds() / 60)
                if duration_minutes != calculated_duration:
                    raise serializers.ValidationError({
                        "duration_minutes": f'Duration minutes ({duration_minutes}) does not match '
                                          f'the time difference ({calculated_duration} minutes).'
                    })

        # Validate scores
        total_score = attrs.get('total_score')
        passing_score = attrs.get('passing_score')
        if total_score is not None and passing_score is not None:
            if passing_score > total_score:
                raise serializers.ValidationError({"passing_score": "Passing score cannot be greater than total score."})

        return attrs

    def create(self, validated_data):
        """
        Create and return a new assessment instance.
        """
        course_id = validated_data.pop('course_id')
        class_instance_id = validated_data.pop('class_instance_id', None)

        course = Course.objects.get(id=course_id)
        validated_data['course'] = course

        if class_instance_id:
            class_instance = Class.objects.get(id=class_instance_id)
            validated_data['class_instance'] = class_instance

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing assessment instance.
        """
        course_id = validated_data.pop('course_id', None)
        if course_id:
            course = Course.objects.get(id=course_id)
            validated_data['course'] = course

        class_instance_id = validated_data.pop('class_instance_id', None)
        if class_instance_id is not None:  # Allow setting to None
            if class_instance_id:
                class_instance = Class.objects.get(id=class_instance_id)
                validated_data['class_instance'] = class_instance
            else:
                validated_data['class_instance'] = None

        return super().update(instance, validated_data)


class PracticeTestSerializer(AssessmentSerializer):
    """
    Serializer for PracticeTest model (inherits from AssessmentSerializer).
    """
    class Meta(AssessmentSerializer.Meta):
        model = PracticeTest
        # Inherits all fields from AssessmentSerializer.Meta


class MockTestSerializer(AssessmentSerializer):
    """
    Serializer for MockTest model (inherits from AssessmentSerializer).
    """
    class Meta(AssessmentSerializer.Meta):
        model = MockTest
        # Inherits all fields from AssessmentSerializer.Meta


class TestScoreSerializer(serializers.ModelSerializer):
    """
    Serializer for TestScore model.
    """
    assessment = serializers.StringRelatedField(read_only=True)
    assessment_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = TestScore
        fields = ['id', 'assessment', 'assessment_id', 'component_name', 'max_score', 'weight']
        read_only_fields = ['id']

    def validate_assessment_id(self, value):
        """
        Validate that the assessment exists.
        """
        try:
            Assessment.objects.get(id=value)
        except Assessment.DoesNotExist:
            raise serializers.ValidationError("Assessment does not exist.")
        return value

    def create(self, validated_data):
        """
        Create and return a new test score component.
        """
        assessment_id = validated_data.pop('assessment_id')
        assessment = Assessment.objects.get(id=assessment_id)
        validated_data['assessment'] = assessment
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing test score component.
        """
        assessment_id = validated_data.pop('assessment_id', None)
        if assessment_id:
            assessment = Assessment.objects.get(id=assessment_id)
            validated_data['assessment'] = assessment
        return super().update(instance, validated_data)


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    """
    Serializer for AssessmentAttempt model.
    """
    assessment = serializers.StringRelatedField(read_only=True)
    assessment_id = serializers.UUIDField(write_only=True)
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Computed properties from save method
    percentage_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    is_passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'assessment', 'assessment_id', 'student', 'student_id',
            'attempt_number', 'started_at', 'submitted_at', 'graded_at',
            'status', 'total_score_achieved', 'percentage_score', 'is_passed',
            'student_feedback', 'instructor_feedback', 'notes',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_assessment_id(self, value):
        """
        Validate that the assessment exists.
        """
        try:
            Assessment.objects.get(id=value)
        except Assessment.DoesNotExist:
            raise serializers.ValidationError("Assessment does not exist.")
        return value

    def validate_student_id(self, value):
        """
        Validate that the student exists.
        """
        try:
            Student.objects.get(id=value)
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student does not exist.")
        return value

    def validate(self, attrs):
        """
        Validate the assessment attempt data.
        """
        # Ensure attempt_number is positive
        attempt_number = attrs.get('attempt_number')
        if attempt_number is not None and attempt_number < 1:
            raise serializers.ValidationError({"attempt_number": "Attempt number must be positive."})

        # Validate score consistency
        total_score_achieved = attrs.get('total_score_achieved')
        assessment_id = attrs.get('assessment_id')

        if total_score_achieved is not None and assessment_id:
            try:
                assessment = Assessment.objects.get(id=assessment_id)
                if total_score_achieved > assessment.total_score:
                    raise serializers.ValidationError({
                        "total_score_achieved": f"Score achieved ({total_score_achieved}) cannot exceed "
                                              f"total score ({assessment.total_score})."
                    })
            except Assessment.DoesNotExist:
                pass  # Will be caught by validate_assessment_id

        # Validate status transitions
        status = attrs.get('status')
        instance = getattr(self, 'instance', None)

        if instance and status:
            # Define valid status transitions
            valid_transitions = {
                'started': ['in_progress'],
                'in_progress': ['completed', 'submitted'],
                'completed': ['graded'],
                'submitted': ['graded'],
                'graded': ['reviewed'],
                'reviewed': []  # Final state
            }

            if status not in valid_transitions.get(instance.status, []):
                raise serializers.ValidationError({
                    "status": f"Invalid status transition from {instance.status} to {status}"
                })

        return attrs

    def create(self, validated_data):
        """
        Create and return a new assessment attempt.
        """
        assessment_id = validated_data.pop('assessment_id')
        student_id = validated_data.pop('student_id')

        assessment = Assessment.objects.get(id=assessment_id)
        student = Student.objects.get(id=student_id)
        validated_data['assessment'] = assessment
        validated_data['student'] = student

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing assessment attempt.
        """
        assessment_id = validated_data.pop('assessment_id', None)
        if assessment_id:
            assessment = Assessment.objects.get(id=assessment_id)
            validated_data['assessment'] = assessment

        student_id = validated_data.pop('student_id', None)
        if student_id:
            student = Student.objects.get(id=student_id)
            validated_data['student'] = student

        return super().update(instance, validated_data)


class ComponentScoreSerializer(serializers.ModelSerializer):
    """
    Serializer for ComponentScore model.
    """
    attempt = serializers.StringRelatedField(read_only=True)
    attempt_id = serializers.UUIDField(write_only=True)
    test_score = serializers.StringRelatedField(read_only=True)
    test_score_id = serializers.UUIDField(write_only=True)

    # Computed properties
    percentage_score = serializers.SerializerMethodField()

    class Meta:
        model = ComponentScore
        fields = [
            'id', 'attempt', 'attempt_id', 'test_score', 'test_score_id',
            'score_achieved', 'percentage_score'
        ]
        read_only_fields = ['id']

    def get_percentage_score(self, obj):
        """Get percentage score for this component."""
        return obj.percentage_score

    def validate_attempt_id(self, value):
        """
        Validate that the attempt exists.
        """
        try:
            AssessmentAttempt.objects.get(id=value)
        except AssessmentAttempt.DoesNotExist:
            raise serializers.ValidationError("Assessment attempt does not exist.")
        return value

    def validate_test_score_id(self, value):
        """
        Validate that the test score component exists.
        """
        try:
            TestScore.objects.get(id=value)
        except TestScore.DoesNotExist:
            raise serializers.ValidationError("Test score component does not exist.")
        return value

    def validate(self, attrs):
        """
        Validate the component score data.
        """
        # Ensure score is within valid range
        score_achieved = attrs.get('score_achieved')
        test_score_id = attrs.get('test_score_id')

        if score_achieved is not None and test_score_id:
            try:
                test_score = TestScore.objects.get(id=test_score_id)
                if score_achieved > test_score.max_score:
                    raise serializers.ValidationError({
                        "score_achieved": f"Score achieved ({score_achieved}) cannot exceed "
                                        f"maximum score ({test_score.max_score}) for this component."
                    })
            except TestScore.DoesNotExist:
                pass  # Will be caught by validate_test_score_id

        # Ensure this combination doesn't already exist (for updates, exclude current instance)
        attempt_id = attrs.get('attempt_id')
        test_score_id = attrs.get('test_score_id')
        instance = getattr(self, 'instance', None)

        if attempt_id and test_score_id:
            queryset = ComponentScore.objects.filter(
                attempt_id=attempt_id,
                test_score_id=test_score_id
            )
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    "test_score_id": "A score for this component already exists for this attempt."
                })

        return attrs

    def create(self, validated_data):
        """
        Create and return a new component score.
        """
        attempt_id = validated_data.pop('attempt_id')
        test_score_id = validated_data.pop('test_score_id')

        attempt = AssessmentAttempt.objects.get(id=attempt_id)
        test_score = TestScore.objects.get(id=test_score_id)
        validated_data['attempt'] = attempt
        validated_data['test_score'] = test_score

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing component score.
        """
        attempt_id = validated_data.pop('attempt_id', None)
        if attempt_id:
            attempt = AssessmentAttempt.objects.get(id=attempt_id)
            validated_data['attempt'] = attempt

        test_score_id = validated_data.pop('test_score_id', None)
        if test_score_id:
            test_score = TestScore.objects.get(id=test_score_id)
            validated_data['test_score'] = test_score

        return super().update(instance, validated_data)


class TargetBandSerializer(serializers.ModelSerializer):
    """
    Serializer for TargetBand model.
    """
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = TargetBand
        fields = [
            'id', 'student', 'student_id',
            'overall_band_score', 'listening_target', 'reading_target',
            'writing_target', 'speaking_target',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_student_id(self, value):
        """
        Validate that the student exists.
        """
        try:
            Student.objects.get(id=value)
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student does not exist.")
        return value

    def validate(self, attrs):
        """
        Validate the target band data.
        """
        # Validate score ranges
        score_fields = ['overall_band_score', 'listening_target', 'reading_target',
                       'writing_target', 'speaking_target']

        for field in score_fields:
            value = attrs.get(field)
            if value is not None:
                if value < 0 or value > 9:
                    raise serializers.ValidationError({
                        field: f"{field.replace('_', ' ').title()} must be between 0 and 9."
                    })

        # Validate that at least overall_band_score is provided
        overall_band_score = attrs.get('overall_band_score')
        if overall_band_score is None:
            raise serializers.ValidationError({
                "overall_band_score": "Overall band score is required."
            })

        return attrs

    def create(self, validated_data):
        """
        Create and return a new target band.
        """
        student_id = validated_data.pop('student_id')
        student = Student.objects.get(id=student_id)
        validated_data['student'] = student
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing target band.
        """
        student_id = validated_data.pop('student_id', None)
        if student_id:
            student = Student.objects.get(id=student_id)
            validated_data['student'] = student
        return super().update(instance, validated_data)