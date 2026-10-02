from django.contrib import admin
from .models import DocumentType, DocumentCategory, DocumentTemplate, BulkDocumentOperation
from apps.courses.models import Course, Class
from apps.students.models import Student
from apps.accounts.models import User


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'is_required', 'max_file_size_mb',
        'allowed_extensions', 'display_order'
    ]
    list_filter = [
        'is_required', 'created_at'
    ]
    search_fields = [
        'name', 'description'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['created_by', 'updated_by']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('File Validation', {
            'fields': ('allowed_extensions', 'max_file_size_mb')
        }),
        ('Requirements & Display', {
            'fields': ('is_required', 'display_order')
        }),
        ('Metadata', {
            'fields': (
                'id', 'created_by', 'updated_by',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related(
            'created_by', 'updated_by'
        )


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'description', 'display_order'
    ]
    list_filter = [
        'created_at'
    ]
    search_fields = [
        'name', 'description'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['created_by', 'updated_by']


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'is_active'
    ]
    list_filter = [
        'template_type', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'description'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['created_by', 'updated_by']

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'description')
        }),
        ('File & Variables', {
            'fields': ('template_file', 'template_variables')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': (
                'id', 'created_by', 'updated_by',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related(
            'created_by', 'updated_by'
        )


@admin.register(BulkDocumentOperation)
class BulkDocumentOperationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'operation_type', 'status',
        'progress_percentage', 'is_complete', 'created_at'
    ]
    list_filter = [
        'operation_type', 'status', 'target_all_students',
        'created_at', 'started_at', 'completed_at'
    ]
    search_fields = [
        'name', 'description'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'progress_percentage', 'is_complete'
    ]
    autocomplete_fields = [
        'target_course', 'target_class', 'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Operation Information', {
            'fields': ('name', 'operation_type', 'description')
        }),
        ('Target Audience', {
            'fields': ('target_all_students', 'target_course', 'target_class')
        }),
        ('Document Types', {
            'fields': ('document_types',)
        }),
        ('Progress Tracking', {
            'fields': ('total_items', 'processed_items', 'failed_items')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Results & Status', {
            'fields': ('results_summary', 'status')
        }),
        ('Metadata', {
            'fields': (
                'id', 'created_by', 'updated_by',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related(
            'target_course', 'target_class', 'created_by', 'updated_by'
        ).prefetch_related('document_types')