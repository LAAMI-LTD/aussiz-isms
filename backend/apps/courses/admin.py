from django.contrib import admin
from .models import CourseCategory, Course, Class


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


class ClassInline(admin.StackedInline):
    model = Class
    extra = 0
    fields = ('name', 'start_date', 'end_date', 'status', 'is_active')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'name', 'category', 'course_type', 'delivery_mode', 'fee', 'status')
    list_filter = ('category', 'course_type', 'delivery_mode', 'status', 'is_active')
    search_fields = ('course_code', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [ClassInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('course_code', 'name', 'category', 'description')
        }),
        ('Course Details', {
            'fields': ('course_type', 'duration_weeks', 'duration_hours', 'delivery_mode')
        }),
        ('Pricing', {
            'fields': ('fee', 'registration_fee')
        }),
        ('Capacity', {
            'fields': ('minimum_students', 'maximum_students')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'start_date', 'end_date', 'status', 'is_active', 'student_count')
    list_filter = ('status', 'is_active', 'start_date', 'course__course_type')
    search_fields = ('course__name', 'name', 'course__course_code')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('Class Information', {
            'fields': ('course', 'name')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def student_count(self, obj):
        return obj.student_count
    student_count.short_description = 'Enrolled Students'