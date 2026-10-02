from django.contrib import admin
from .models import ReportCategory, ReportTemplate, GeneratedReport, ReportSchedule
from apps.accounts.models import User


class ReportTemplateInline(admin.TabularInline):
    """
    Inline for displaying report templates in the category admin.
    """
    model = ReportTemplate
    extra = 0
    show_change_link = True


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [ReportTemplateInline]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('created_by', 'updated_by')


class GeneratedReportInline(admin.TabularInline):
    """
    Inline for displaying generated reports in the template admin.
    """
    model = GeneratedReport
    extra = 0
    show_change_link = True
    readonly_fields = ['report_number', 'name', 'status', 'generated_at']


class ReportScheduleInline(admin.TabularInline):
    """
    Inline for displaying report schedules in the template admin.
    """
    model = ReportSchedule
    extra = 0
    show_change_link = True
    readonly_fields = ['name', 'frequency', 'is_active', 'next_generation_at']


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'category', 'format',
        'is_active', 'is_scheduled', 'created_at'
    ]
    list_filter = [
        'category', 'report_type', 'format', 'is_active', 'is_scheduled', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [GeneratedReportInline, ReportScheduleInline]

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'report_type', 'category', 'description')
        }),
        ('Configuration', {
            'fields': ('format', 'is_active', 'is_scheduled', 'parameters_schema')
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
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'category', 'created_by', 'updated_by'
        )


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_number', 'template', 'status', 'format',
        'generated_at', 'file_size', 'is_ready'
    ]
    list_filter = [
        'status', 'format', 'generated_at', 'template__category'
    ]
    search_fields = [
        'name', 'description', 'report_number', 'template__name'
    ]
    readonly_fields = [
        'id', 'report_number', 'generated_at', 'generation_started_at',
        'generation_completed_at', 'generated_by', 'created_at', 'updated_at',
        'created_by', 'updated_by', 'file', 'file_size', 'is_ready', 'generation_duration'
    ]
    autocomplete_fields = ['template', 'generated_by', 'created_by', 'updated_by']

    fieldsets = (
        ('Report Information', {
            'fields': ('report_number', 'name', 'template', 'description')
        }),
        ('Generation Details', {
            'fields': ('status', 'format', 'parameters')
        }),
        ('Output', {
            'fields': ('file', 'file_size')
        }),
        ('Timing', {
            'fields': (
                'generation_started_at', 'generation_completed_at',
                'generation_duration'
            )
        }),
        ('Metadata', {
            'fields': (
                'id', 'generated_by', 'created_by', 'updated_by',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'template', 'generated_by', 'created_by', 'updated_by'
        )


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template', 'frequency', 'time_of_day',
        'is_active', 'last_generated_at', 'next_generation_at'
    ]
    list_filter = [
        'frequency', 'is_active', 'last_generated_at', 'next_generation_at',
        'template__category'
    ]
    search_fields = ['name', 'description', 'template__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'last_generated_at', 'next_generation_at'
    ]
    autocomplete_fields = ['template', 'created_by', 'updated_by']

    fieldsets = (
        ('Schedule Information', {
            'fields': ('name', 'template', 'description')
        }),
        ('Schedule Details', {
            'fields': ('frequency', 'day_of_week', 'day_of_month', 'time_of_day')
        }),
        ('Parameters', {
            'fields': ('parameters',)
        }),
        ('Status', {
            'fields': ('is_active', 'last_generated_at', 'next_generation_at')
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
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'template', 'created_by', 'updated_by'
        )