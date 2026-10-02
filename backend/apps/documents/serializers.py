from rest_framework import serializers
from .models import DocumentType, DocumentCategory, DocumentTemplate, BulkDocumentOperation
from apps.students.models import Student
from apps.courses.models import Course, Class
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


class DocumentTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for DocumentType model.
    """
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = DocumentType
        fields = [
            'id', 'name', 'description', 'allowed_extensions',
            'max_file_size_mb', 'is_required', 'display_order',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_allowed_extensions(self, value):
        """
        Validate that allowed extensions is a comma-separated list.
        """
        if value:
            # Convert to lowercase and strip whitespace
            extensions = [ext.strip().lower() for ext in value.split(',') if ext.strip()]
            # Validate each extension
            for ext in extensions:
                if not ext.isalpha():
                    raise serializers.ValidationError(
                        f"Extension '{ext}' must contain only letters."
                    )
            # Return normalized format
            return ','.join(extensions)
        return value

    def validate_max_file_size_mb(self, value):
        """
        Validate that max file size is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Maximum file size must be greater than 0 MB.")
        return value


class DocumentCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for DocumentCategory model.
    """
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'name', 'description', 'display_order',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for DocumentTemplate model.
    """
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'template_type', 'description',
            'template_file', 'template_variables', 'is_active',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_template_file(self, value):
        """
        Validate template file.
        """
        # File validation is handled by FileExtensionValidator in the model
        return value

    def validate_template_variables(self, value):
        """
        Validate that template_variables is valid JSON if provided.
        """
        if value:
            import json
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Template variables must be valid JSON.")
        return value


class BulkDocumentOperationSerializer(serializers.ModelSerializer):
    """
    Serializer for BulkDocumentOperation model.
    """
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    target_course = serializers.StringRelatedField(read_only=True)
    target_course_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    target_class = serializers.StringRelatedField(read_only=True)
    target_class_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    document_types = serializers.StringRelatedField(many=True, read_only=True)
    document_type_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    # Computed properties
    progress_percentage = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()

    class Meta:
        model = BulkDocumentOperation
        fields = [
            'id', 'name', 'operation_type', 'description',
            'target_all_students', 'target_course', 'target_course_id',
            'target_class', 'target_class_id', 'document_types', 'document_type_ids',
            'status', 'total_items', 'processed_items', 'failed_items',
            'results_summary', 'started_at', 'completed_at',
            'created_by', 'updated_by', 'created_at', 'updated_at',
            'progress_percentage', 'is_complete'
        ]
        read_only_fields = [
            'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
            'progress_percentage', 'is_complete'
        ]

    def get_progress_percentage(self, obj):
        """Get completion percentage."""
        return obj.progress_percentage

    def get_is_complete(self, obj):
        """Check if operation is complete."""
        return obj.is_complete

    def validate_target_course_id(self, value):
        """
        Validate that the course exists.
        """
        try:
            Course.objects.get(id=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist.")
        return value

    def validate_target_class_id(self, value):
        """
        Validate that the class exists.
        """
        try:
            Class.objects.get(id=value)
        except Class.DoesNotExist:
            raise serializers.ValidationError("Class does not exist.")
        return value

    def validate_document_type_ids(self, value):
        """
        Validate that all document type IDs exist.
        """
        from .models import DocumentType
        for doc_type_id in value:
            try:
                DocumentType.objects.get(id=doc_type_id)
            except DocumentType.DoesNotExist:
                raise serializers.ValidationError(f"Document type with ID {doc_type_id} does not exist.")
        return value

    def validate(self, attrs):
        """
        Validate the bulk document operation data.
        """
        # Ensure at least one target is specified
        target_all_students = attrs.get('target_all_students', False)
        target_course_id = attrs.get('target_course_id')
        target_class_id = attrs.get('target_class_id')

        if not target_all_students and not target_course_id and not target_class_id:
            raise serializers.ValidationError({
                'non_field_errors': 'At least one target must be specified: all students, course, or class.'
            })

        # Ensure total_items is non-negative
        total_items = attrs.get('total_items', 0)
        if total_items < 0:
            raise serializers.ValidationError({
                'total_items': 'Total items must be greater than or equal to 0.'
            })

        # Ensure processed_items and failed_items are non-negative and not exceeding total_items
        processed_items = attrs.get('processed_items', 0)
        failed_items = attrs.get('failed_items', 0)
        if processed_items < 0:
            raise serializers.ValidationError({
                'processed_items': 'Processed items must be greater than or equal to 0.'
            })
        if failed_items < 0:
            raise serializers.ValidationError({
                'failed_items': 'Failed items must be greater than or equal to 0.'
            })
        if processed_items + failed_items > total_items:
            raise serializers.ValidationError({
                'non_field_errors': 'Processed items plus failed items cannot exceed total items.'
            })

        # Validate status transitions for updates
        status = attrs.get('status')
        instance = getattr(self, 'instance', None)

        if instance and status:
            # Define valid status transitions
            valid_transitions = {
                'pending': ['processing', 'cancelled'],
                'processing': ['completed', 'failed', 'cancelled'],
                'completed': [],  # Final state
                'failed': [],     # Final state
                'cancelled': []   # Final state
            }

            if status not in valid_transitions.get(instance.status, []):
                raise serializers.ValidationError({
                    'status': f'Invalid status transition from {instance.status} to {status}'
                })

        return attrs

    def create(self, validated_data):
        """
        Create and return a new bulk document operation.
        """
        target_course_id = validated_data.pop('target_course_id', None)
        target_class_id = validated_data.pop('target_class_id', None)
        document_type_ids = validated_data.pop('document_type_ids', [])

        if target_course_id:
            target_course = Course.objects.get(id=target_course_id)
            validated_data['target_course'] = target_course

        if target_class_id:
            target_class = Class.objects.get(id=target_class_id)
            validated_data['target_class'] = target_class

        # Create the operation
        operation = BulkDocumentOperation.objects.create(**validated_data)

        # Set document types many-to-many relationship
        if document_type_ids:
            document_types = DocumentType.objects.filter(id__in=document_type_ids)
            operation.document_types.set(document_types)

        return operation

    def update(self, instance, validated_data):
        """
        Update and return an existing bulk document operation.
        """
        target_course_id = validated_data.pop('target_course_id', None)
        target_class_id = validated_data.pop('target_class_id', None)
        document_type_ids = validated_data.pop('document_type_ids', None)

        if target_course_id is not None:
            if target_course_id:
                target_course = Course.objects.get(id=target_course_id)
                validated_data['target_course'] = target_course
            else:
                validated_data['target_course'] = None

        if target_class_id is not None:
            if target_class_id:
                target_class = Class.objects.get(id=target_class_id)
                validated_data['target_class'] = target_class
            else:
                validated_data['target_class'] = None

        # Update the operation instance
        operation = super().update(instance, validated_data)

        # Update document types many-to-many relationship if provided
        if document_type_ids is not None:
            document_types = DocumentType.objects.filter(id__in=document_type_ids)
            operation.document_types.set(document_types)

        return operation