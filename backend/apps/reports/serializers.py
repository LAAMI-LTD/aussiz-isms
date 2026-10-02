from rest_framework import serializers
from .models import ReportCategory, ReportTemplate, GeneratedReport, ReportSchedule
from apps.students.models import Student
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


class ReportCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for ReportCategory model.
    """
    class Meta:
        model = ReportCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 'is_active',
                  'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ReportTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for ReportTemplate model.
    """
    category = ReportCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'report_type', 'category', 'category_id', 'description',
            'format', 'is_active', 'is_scheduled', 'parameters_schema',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate_parameters_schema(self, value):
        """Validate that parameters_schema is valid JSON schema."""
        if value is not None:
            # Basic validation - in a real implementation, you might use a JSON schema validator
            if not isinstance(value, dict):
                raise serializers.ValidationError("Parameters schema must be a JSON object.")
        return value


class GeneratedReportSerializer(serializers.ModelSerializer):
    """
    Serializer for GeneratedReport model.
    """
    template = ReportTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True)
    generated_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = GeneratedReport
        fields = [
            'id', 'template', 'template_id', 'report_number', 'name', 'description',
            'status', 'format', 'parameters', 'file', 'file_size',
            'generated_at', 'generation_started_at', 'generation_completed_at',
            'generated_by', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'is_ready', 'generation_duration'
        ]
        read_only_fields = [
            'id', 'report_number', 'generated_at', 'generation_started_at',
            'generation_completed_at', 'generated_by', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'file', 'file_size', 'is_ready', 'generation_duration'
        ]

    def validate_parameters(self, value):
        """Validate that parameters match the template's schema."""
        # In a real implementation, you would validate against the template's parameters_schema
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a JSON object.")
        return value


class ReportScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for ReportSchedule model.
    """
    template = ReportTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'template', 'template_id', 'name', 'description', 'frequency',
            'day_of_week', 'day_of_month', 'time_of_day', 'parameters',
            'is_active', 'last_generated_at', 'next_generation_at',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by',
                           'last_generated_at', 'next_generation_at']

    def validate(self, attrs):
        """Validate schedule data based on frequency."""
        frequency = attrs.get('frequency')
        day_of_week = attrs.get('day_of_week')
        day_of_month = attrs.get('day_of_month')

        # Validate day_of_week for weekly frequency
        if frequency == 'weekly' and day_of_week is None:
            raise serializers.ValidationError({
                'day_of_week': 'Day of week is required for weekly reports.'
            })
        elif frequency != 'weekly' and day_of_week is not None:
            raise serializers.ValidationError({
                'day_of_week': 'Day of week is only applicable for weekly reports.'
            })

        # Validate day_of_month for monthly frequency
        if frequency == 'monthly' and day_of_month is None:
            raise serializers.ValidationError({
                'day_of_month': 'Day of month is required for monthly reports.'
            })
        elif frequency != 'monthly' and day_of_month is not None:
            raise serializers.ValidationError({
                'day_of_month': 'Day of month is only applicable for monthly reports.'
            })

        return attrs