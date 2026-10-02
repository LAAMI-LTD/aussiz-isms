from django.contrib import admin
from .models import Assessment, PracticeTest, MockTest, TestScore, AssessmentAttempt, ComponentScore, TargetBand
from apps.courses.models import Course
from apps.students.models import Student


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'assessment_type', 'course', 'scheduled_date',
        'start_time', 'end_time', 'total_score', 'passing_score',
        'is_active', 'is_available'
    ]
    list_filter = [
        'assessment_type', 'is_active', 'is_available',
        'scheduled_date', 'course__category', 'course__course_type'
    ]
    search_fields = [
        'name', 'description', 'course__name', 'course__course_code'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'is_passing_score'
    ]
    autocomplete_fields = ['course', 'class_instance', 'created_by', 'updated_by']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'assessment_type', 'description')
        }),
        ('Course & Schedule', {
            'fields': ('course', 'class_instance', 'scheduled_date', 'start_time', 'end_time')
        }),
        ('Duration & Timing', {
            'fields': ('duration_minutes', 'instructions', 'materials_required')
        }),
        ('Scoring', {
            'fields': ('total_score', 'passing_score')
        }),
        ('Availability', {
            'fields': ('is_active', 'is_available')
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
            'course', 'class_instance', 'created_by', 'updated_by'
        )


@admin.register(PracticeTest)
class PracticeTestAdmin(AssessmentAdmin):
    pass


@admin.register(MockTest)
class MockTestAdmin(AssessmentAdmin):
    pass


@admin.register(TestScore)
class TestScoreAdmin(admin.ModelAdmin):
    list_display = [
        'assessment', 'component_name', 'max_score', 'weight'
    ]
    list_filter = [
        'assessment__assessment_type', 'assessment__course'
    ]
    search_fields = [
        'assessment__name', 'component_name'
    ]
    readonly_fields = ['id']
    autocomplete_fields = ['assessment']

    fieldsets = (
        ('Component Information', {
            'fields': ('assessment', 'component_name')
        }),
        ('Scoring Details', {
            'fields': ('max_score', 'weight')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'assessment', 'attempt_number', 'status',
        'percentage_score', 'is_passed', 'started_at'
    ]
    list_filter = [
        'status', 'is_passed', 'started_at', 'submitted_at',
        'assessment__assessment_type', 'assessment__course'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'assessment__name', 'assessment__course__name'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'percentage_score', 'is_passed'
    ]
    autocomplete_fields = [
        'assessment', 'student', 'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Attempt Information', {
            'fields': ('assessment', 'student', 'attempt_number')
        }),
        ('Timing', {
            'fields': ('started_at', 'submitted_at', 'graded_at')
        }),
        ('Status & Results', {
            'fields': ('status', 'total_score_achieved', 'percentage_score', 'is_passed')
        }),
        ('Feedback', {
            'fields': ('student_feedback', 'instructor_feedback', 'notes')
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
            'assessment', 'student', 'created_by', 'updated_by'
        )


@admin.register(ComponentScore)
class ComponentScoreAdmin(admin.ModelAdmin):
    list_display = [
        'attempt', 'test_score', 'score_achieved', 'percentage_score'
    ]
    list_filter = [
        'attempt__assessment__assessment_type',
        'test_score__component_name'
    ]
    search_fields = [
        'attempt__student__first_name', 'attempt__student__last_name',
        'attempt__assessment__name', 'test_score__component_name'
    ]
    readonly_fields = ['id', 'percentage_score']
    autocomplete_fields = ['attempt', 'test_score']

    fieldsets = (
        ('Score Information', {
            'fields': ('attempt', 'test_score', 'score_achieved')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TargetBand)
class TargetBandAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'overall_band_score', 'listening_target',
        'reading_target', 'writing_target', 'speaking_target'
    ]
    list_filter = [
        'overall_band_score', 'listening_target', 'reading_target',
        'writing_target', 'speaking_target'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'student__email'
    ]
    readonly_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']
    autocomplete_fields = ['student', 'created_by', 'updated_by']

    fieldsets = (
        ('Target Information', {
            'fields': ('student', 'overall_band_score')
        }),
        ('Component Targets (Optional)', {
            'fields': (
                'listening_target', 'reading_target',
                'writing_target', 'speaking_target'
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
            'student', 'created_by', 'updated_by'
        )