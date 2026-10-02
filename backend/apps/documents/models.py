from django.db import models
import uuid
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from apps.students.models import Student, StudentDocument
from apps.accounts.models import User


class DocumentType(models.Model):
    """
    Types of documents that can be uploaded/stored.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # File validation
    allowed_extensions = models.CharField(
        max_length=200,
        default='pdf,jpg,jpeg,png,doc,docx',
        help_text='Comma-separated list of allowed file extensions (e.g., pdf,jpg,doc)'
    )
    max_file_size_mb = models.PositiveIntegerField(
        default=10,
        help_text='Maximum file size in megabytes'
    )
    is_required = models.BooleanField(
        default=False,
        help_text='Whether this document type is required for all students'
    )
    # Display order
    display_order = models.PositiveIntegerField(default=0)
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_types_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_types_updated')

    class Meta:
        db_table = 'document_types'
        verbose_name = 'Document Type'
        verbose_name_plural = 'Document Types'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    @property
    def allowed_extensions_list(self):
        """Get allowed extensions as a list."""
        if self.allowed_extensions:
            return [ext.strip().lower() for ext in self.allowed_extensions.split(',')]
        return []


class DocumentCategory(models.Model):
    """
    Categories for grouping documents.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_categories_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_categories_updated')

    class Meta:
        db_table = 'document_categories'
        verbose_name = 'Document Category'
        verbose_name_plural = 'Document Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class DocumentTemplate(models.Model):
    """
    Templates for document generation.
    """
    TEMPLATE_TYPES = [
        ('letter', 'Letter'),
        ('form', 'Form'),
        ('certificate', 'Certificate'),
        ('report', 'Report'),
        ('receipt', 'Receipt'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    description = models.TextField(blank=True)
    # File field for template storage
    template_file = models.FileField(
        upload_to='document_templates/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['doc', 'docx', 'pdf'])]
    )
    # Variables that can be used in template (JSON format)
    template_variables = models.TextField(
        blank=True,
        help_text='JSON string of variables available in template (e.g., {"student_name": "Full name", "student_id": "Student ID"})'
    )
    is_active = models.BooleanField(default=True)
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_templates_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_templates_updated')

    class Meta:
        db_table = 'document_templates'
        verbose_name = 'Document Template'
        verbose_name_plural = 'Document Templates'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class BulkDocumentOperation(models.Model):
    """
    Records of bulk document operations (e.g., sending documents to multiple students).
    """
    OPERATION_TYPES = [
        ('send', 'Send Documents'),
        ('request', 'Request Documents'),
        ('verify', 'Verify Documents'),
        ('archive', 'Archive Documents'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    description = models.TextField(blank=True)
    # Related documents/types
    document_types = models.ManyToManyField(DocumentType, blank=True, related_name='bulk_operations')
    # Target audience
    target_all_students = models.BooleanField(default=False)
    target_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_bulk_operations'
    )
    target_class = models.ForeignKey(
        'courses.Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_bulk_operations'
    )
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_items = models.PositiveIntegerField(default=0, help_text='Total number of items/documents to process')
    processed_items = models.PositiveIntegerField(default=0, help_text='Number of items already processed')
    failed_items = models.PositiveIntegerField(default=0, help_text='Number of items that failed')
    # Results
    results_summary = models.TextField(blank=True, help_text='Summary of operation results')
    # Metadata
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bulk_doc_ops_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bulk_doc_ops_updated')

    class Meta:
        db_table = 'bulk_document_operations'
        verbose_name = 'Bulk Document Operation'
        verbose_name_plural = 'Bulk Document Operations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_operation_type_display()})"

    @property
    def progress_percentage(self):
        """Calculate completion percentage."""
        if self.total_items > 0:
            return (self.processed_items / self.total_items) * 100
        return 0

    @property
    def is_complete(self):
        """Check if operation is complete."""
        return self.status in ['completed', 'failed', 'cancelled']


# Proxy model for StudentDocument to add document-type-specific functionality
class StudentDocumentProxy(StudentDocument):
    """
    Proxy model for StudentDocument to add custom managers/methods.
    This allows us to add document-type specific functionality without
    duplicating the actual storage model.
    """
    class Meta:
        proxy = True
        verbose_name = 'Student Document'
        verbose_name_plural = 'Student Documents'

    def is_valid_file_type(self):
        """
        Check if the document's file type is allowed for its document type.
        This would need to be implemented based on how we link StudentDocument to DocumentType.
        For now, we'll return True as placeholder.
        """
        # TODO: Implement actual validation based on document type
        return True

    def get_file_size_mb(self):
        """Get file size in megabytes."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0