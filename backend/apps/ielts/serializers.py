from rest_framework import serializers
from .models import IELTSTest, IELTSTestSection, IELTSTestAttempt, IELTSTestSectionScore, IELTSProgress
from apps.students.models import Student
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


class IELTSTestSerializer(serializers.ModelSerializer):
    """Serializer for IELTSTest model."""
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSTest
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate(self, attrs):
        """Validate test data."""
        # Ensure time limits are reasonable if sections will be added
        return attrs


class IELTSTestSectionSerializer(serializers.ModelSerializer):
    """Serializer for IELTSTestSection model."""
    test = IELTSTestSerializer(read_only=True)
    test_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = IELTSTestSection
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Validate section data."""
        test_id = attrs.get('test_id')
        section_type = attrs.get('section_type')
        order = attrs.get('order')

        # Check if this section type already exists for this test
        if test_id and section_type:
            existing = IELTSTestSection.objects.filter(
                test_id=test_id,
                section_type=section_type
            ).exclude(
                id=getattr(self.instance, 'id', None)
            ).first()

            if existing:
                raise serializers.ValidationError({
                    'section_type': f'This test already has a {section_type} section.'
                })

        return attrs


class IELTSTestAttemptSerializer(serializers.ModelSerializer):
    """Serializer for IELTSTestAttempt model."""
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    test = IELTSTestSerializer(read_only=True)
    test_id = serializers.UUIDField(write_only=True)
    reviewed_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSTestAttempt
        fields = '__all__'
        read_only_fields = ['id', 'started_at', 'created_at', 'updated_at', 'created_by', 'updated_by', 'reviewed_by']

    def validate(self, attrs):
        """Validate attempt data."""
        student_id = attrs.get('student_id')
        test_id = attrs.get('test_id')
        status = attrs.get('status')
        completed_at = attrs.get('completed_at')
        started_at = attrs.get('started_at')

        # Check if student is already attempting this test (if not completed/cancelled)
        if student_id and test_id and status not in ['completed', 'cancelled']:
            existing_attempt = IELTSTestAttempt.objects.filter(
                student_id=student_id,
                test_id=test_id,
                status__in=['in_progress']
            ).exclude(
                id=getattr(self.instance, 'id', None)
            ).first()

            if existing_attempt:
                raise serializers.ValidationError({
                    'non_field_errors': 'Student already has an in-progress attempt for this test.'
                })

        # Validate dates
        if completed_at and started_at and completed_at < started_at:
            raise serializers.ValidationError({
                'completed_at': 'Completion date cannot be before start date.'
            })

        return attrs

    def create(self, validated_data):
        """Create attempt and calculate band scores if section scores are provided."""
        # Handle section scores if provided in initial data (for nested creation)
        section_scores_data = self.context.get('section_scores', [])

        attempt = IELTSTestAttempt.objects.create(**validated_data)

        # Create section scores if provided
        for score_data in section_scores_data:
            IELTSTestSectionScore.objects.create(attempt=attempt, **score_data)

        # Calculate overall band score if section scores exist
        if section_scores_data:
            attempt.overall_band_score = self._calculate_overall_band(attempt)
            attempt.save()

        return attempt

    def update(self, instance, validated_data):
        """Update attempt and recalculate band scores if needed."""
        # Handle section scores if provided
        section_scores_data = self.context.get('section_scores', [])

        # Update the attempt
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If section scores were provided, update them
        if section_scores_data:
            # Delete existing section scores and recreate
            instance.section_scores.all().delete()
            for score_data in section_scores_data:
                IELTSTestSectionScore.objects.create(attempt=instance, **score_data)

            # Recalculate overall band score
            instance.overall_band_score = self._calculate_overall_band(instance)
            instance.save()

        return instance

    def _calculate_overall_band(self, attempt):
        """Calculate overall band score from section scores."""
        section_scores = attempt.section_scores.all()
        if not section_scores:
            return None

        # IELTS overall band is the average of the 4 section bands, rounded to nearest 0.5
        total_band = sum(score.band_score for score in section_scores)
        average_band = total_band / len(section_scores)

        # Round to nearest 0.5
        rounded_band = round(average_band * 2) / 2
        return min(9.0, max(0.0, rounded_band))  # Ensure within bounds


class IELTSTestSectionScoreSerializer(serializers.ModelSerializer):
    """Serializer for IELTSTestSectionScore model."""
    attempt = IELTSTestAttemptSerializer(read_only=True)
    attempt_id = serializers.UUIDField(write_only=True)
    section = IELTSTestSectionSerializer(read_only=True)
    section_id = serializers.UUIDField(write_only=True)
    reviewed_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSTestSectionScore
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Validate section score data."""
        attempt_id = attrs.get('attempt_id')
        section_id = attrs.get('section_id')
        raw_score = attrs.get('raw_score')
        band_score = attrs.get('band_score')
        percentage_score = attrs.get('percentage_score')

        # Validate that the section belongs to the same test as the attempt
        if attempt_id and section_id:
            try:
                attempt = IELTSTestAttempt.objects.get(id=attempt_id)
                section = IELTSTestSection.objects.get(id=section_id)

                if attempt.test != section.test:
                    raise serializers.ValidationError({
                        'non_field_errors': 'Section does not belong to the same test as the attempt.'
                    })
            except (IELTSTestAttempt.DoesNotExist, IELTSTestSection.DoesNotExist):
                pass  # Will be caught by foreign key validation

        # Validate raw score against section total marks
        if section_id and raw_score is not None:
            try:
                section = IELTSTestSection.objects.get(id=section_id)
                if raw_score > section.total_marks:
                    raise serializers.ValidationError({
                        'raw_score': f'Raw score cannot exceed total marks ({section.total_marks}) for this section.'
                    })
            except IELTSTestSection.DoesNotExist:
                pass  # Will be caught by foreign key validation

        return attrs


class IELTSProgressSerializer(serializers.ModelSerializer):
    """Serializer for IELTSProgress model."""
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSProgress
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate(self, attrs):
        """Validate progress data."""
        target_band_score = attrs.get('target_band_score')
        current_estimated_band = attrs.get('current_estimated_band')

        if target_band_score is not None and (target_band_score < 0.0 or target_band_score > 9.0):
            raise serializers.ValidationError({
                'target_band_score': 'Target band score must be between 0 and 9.'
            })

        if current_estimated_band is not None and (current_estimated_band < 0.0 or current_estimated_band > 9.0):
            raise serializers.ValidationError({
                'current_estimated_band': 'Current estimated band must be between 0 and 9.'
            })

        return attrs