from django.contrib import admin
from .models import AttendanceSession, AttendanceStatus, AttendanceRecord


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ('recorded_at',)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('class_instance', 'session_date', 'session_number', 'topic', 'is_active')
    list_filter = ('is_active', 'session_date', 'class_instance__course__course_type')
    search_fields = ('class_instance__name', 'topic', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [AttendanceRecordInline]

    fieldsets = (
        ('Session Information', {
            'fields': ('class_instance', 'session_date', 'session_number')
        }),
        ('Session Details', {
            'fields': ('topic', 'description', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AttendanceStatus)
class AttendanceStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_present', 'points', 'color')
    list_filter = ('is_present',)
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'recorded_by', 'recorded_at')
    list_filter = ('status', 'recorded_at', 'session__class_instance__course')
    search_fields = ('student__first_name', 'student__last_name', 'session__class_instance__name')
    readonly_fields = ('recorded_at', 'updated_at', 'recorded_by')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'session', 'session__class_instance', 'session__class_instance__course',
            'status', 'recorded_by'
        )