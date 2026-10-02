from django.contrib import admin
from .models import NotificationType, Notification, DeviceToken, NotificationTemplate
from apps.students.models import Student
from apps.accounts.models import User


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'name', 'can_send_email', 'can_send_sms',
        'can_send_push', 'can_send_in_app', 'is_active',
        'is_enabled_for_students', 'is_enabled_for_staff'
    ]
    list_filter = [
        'can_send_email', 'can_send_sms', 'can_send_push', 'can_send_in_app',
        'is_active', 'is_enabled_for_students', 'is_enabled_for_staff',
        'created_at'
    ]
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['created_by', 'updated_by']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Channels', {
            'fields': (
                'can_send_email', 'can_send_sms', 'can_send_push', 'can_send_in_app'
            )
        }),
        ('Templates', {
            'fields': (
                'email_subject_template', 'email_body_template',
                'sms_template', 'push_template', 'in_app_template'
            ),
            'classes': ('collapse',)
        }),
        ('Audience', {
            'fields': (
                'is_enabled_for_students', 'is_enabled_for_staff'
            )
        }),
        ('Settings', {
            'fields': ('cooldown_period_minutes', 'is_active')
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


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient_name', 'notification_type', 'channel',
        'status', 'sent_at', 'created_at'
    ]
    list_filter = [
        'status', 'channel', 'notification_type',
        'sent_at', 'created_at'
    ]
    search_fields = [
        'id',
        'recipient__first_name', 'recipient__last_name', 'recipient__student_id',
        'recipient_staff__first_name', 'recipient_staff__last_name',
        'notification_type__display_name',
        'subject', 'body'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'sent_at', 'delivered_at', 'failed_at', 'failure_reason',
        'recipient_name'
    ]
    autocomplete_fields = [
        'recipient', 'recipient_staff', 'notification_type',
        'related_course', 'related_class',
        'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Recipient Information', {
            'fields': (
                'recipient', 'recipient_staff'
            )
        }),
        ('Notification Details', {
            'fields': (
                'notification_type', 'channel', 'status'
            )
        }),
        ('Content', {
            'fields': ('subject', 'body')
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at', 'failed_at')
        }),
        ('Failure Information', {
            'fields': ('failure_reason',),
            'classes': ('collapse',)
        }),
        ('Related Objects', {
            'fields': (
                'related_course', 'related_class'
            ),
            'classes': ('collapse',)
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
            'recipient', 'recipient__user',
            'recipient_staff',
            'notification_type',
            'related_course', 'related_class',
            'created_by', 'updated_by'
        )

    def recipient_name(self, obj):
        """Display recipient name in list view."""
        return obj.recipient_name
    recipient_name.short_description = 'Recipient'


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'device_type', 'device_name',
        'is_active', 'created_at'
    ]
    list_filter = [
        'device_type', 'is_active', 'created_at'
    ]
    search_fields = [
        'user__first_name', 'user__last_name',
        'device_name', 'device_token'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['user', 'created_by', 'updated_by']

    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'device_type', 'device_token')
        }),
        ('Device Details', {
            'fields': ('device_name',)
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
            'user', 'user__user', 'created_by', 'updated_by'
        )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
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
        ('Template Content', {
            'fields': ('subject_template', 'body_template')
        }),
        ('Template Variables', {
            'fields': ('template_variables', 'example_data'),
            'classes': ('collapse',)
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