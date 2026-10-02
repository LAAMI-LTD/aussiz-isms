from rest_framework import serializers
from .models import IELTSResult, IELTSResultVerification, IELTSResultAudit
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest, IELTSTestAttempt


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
    """Serializer for IELTSTest model (nested)."""
    class Meta:
        model = IELTSTest
        fields = ['id', 'title', 'test_type', 'test_mode']
        read_only_fields = fields


class IELTSTestAttemptSerializer(serializers.ModelSerializer):
    """Serializer for IELTSTestAttempt model (nested)."""
    class Meta:
        model = IELTSTestAttempt
        fields = ['id', 'status', 'overall_band_score']
        read_only_fields = fields


class IELTSResultSerializer(serializers.ModelSerializer):
    """Serializer for IELTSResult model."""
    student = StudentSerializer(read_only=True)
    test = IELTSTestSerializer(read_only=True)
    attempt = IELTSTestAttemptSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    last_verified_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSResult
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate(self, attrs):
        """Validate result data."""
        # Extract section scores
        listening = attrs.get('listening_band_score')
        reading = attrs.get('reading_band_score')
        writing = attrs.get('writing_band_score')
        speaking = attrs.get('speaking_band_score')
        overall = attrs.get('overall_band_score')

        # If all section scores are provided, validate overall score
        if all(score is not None for score in [listening, reading, writing, speaking]):
            # Calculate expected overall band score
            average_band = (listening + reading + writing + speaking) / 4
            expected_overall = round(average_band * 2) / 2

            # If overall score is provided, check if it matches expected
            if overall is not None and abs(overall - expected_overall) > 0.1:
                raise serializers.ValidationError({
                    'overall_band_score': f'Overall band score should be {expected_overall} '
                                        f'(average of section scores).'
                })

        # Validate expiry date
        expiry_date = attrs.get('expiry_date')
        release_date = attrs.get('release_date')
        if expiry_date and release_date and expiry_date < release_date.date():
            raise serializers.ValidationError({
                'expiry_date': 'Expiry date cannot be before release date.'
            })

        return attrs


class IELTSResultVerificationSerializer(serializers.ModelSerializer):
    """Serializer for IELTSResultVerification model."""
    result = IELTSResultSerializer(read_only=True)
    result_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSResultVerification
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate(self, attrs):
        """Validate verification request data."""
        result_id = attrs.get('result_id')
        status = attrs.get('status')

        # Check if result exists and is available for verification
        if result_id:
            try:
                result = IELTSResult.objects.get(id=result_id)
                if result.result_status != 'released':
                    raise serializers.ValidationError({
                        'result_id': 'Can only verify released results.'
                    })
                if result.is_expired:
                    raise serializers.ValidationError({
                        'result_id': 'Cannot verify expired results.'
                    })
            except IELTSResult.DoesNotExist:
                raise serializers.ValidationError({
                    'result_id': 'Invalid result ID.'
                })

        return attrs


class IELTSResultAuditSerializer(serializers.ModelSerializer):
    """Serializer for IELTSResultAudit model."""
    result = IELTSResultSerializer(read_only=True)
    result_id = serializers.UUIDField(write_only=True)
    changed_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSResultAudit
        fields = '__all__'
        read_only_fields = ['id', 'changed_at', 'changed_by']