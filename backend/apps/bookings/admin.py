from django.contrib import admin
from .models import IELTSExamCenter, IELTSExamDate, IELTSExamBooking
from apps.students.models import Student
from apps.accounts.models import User


@admin.register(IELTSExamCenter)
class IELTSExamCenterAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'city', 'country', 'daily_capacity', 'is_active',
        'created_at'
    ]
    list_filter = [
        'city', 'country', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'address', 'city', 'country'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['created_by', 'updated_by']

    fieldsets = (
        ('Center Information', {
            'fields': ('name', 'address', 'city', 'country')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'website')
        }),
        ('Capacity', {
            'fields': ('daily_capacity',)
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


@admin.register(IELTSExamDate)
class IELTSExamDateAdmin(admin.ModelAdmin):
    list_display = [
        'center', 'exam_date', 'exam_type', 'registration_deadline',
        'total_slots', 'filled_slots', 'available_slots', 'exam_fee',
        'is_active'
    ]
    list_filter = [
        'exam_type', 'is_active', 'exam_date', 'registration_deadline',
        'center__city', 'center__country'
    ]
    search_fields = [
        'center__name', 'center__city', 'center__country'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'filled_slots', 'available_slots'
    ]
    autocomplete_fields = ['center', 'created_by', 'updated_by']

    fieldsets = (
        ('Exam Information', {
            'fields': ('center', 'exam_type', 'exam_date')
        }),
        ('Registration', {
            'fields': ('registration_deadline', 'total_slots')
        }),
        ('Capacity', {
            'fields': ('filled_slots', 'available_slots')
        }),
        ('Fee', {
            'fields': ('exam_fee',)
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
            'center', 'center__created_by', 'center__updated_by',
            'created_by', 'updated_by'
        )


@admin.register(IELTSExamBooking)
class IELTSExamBookingAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'exam_date', 'status', 'amount_paid',
        'exam_attended', 'booking_date'
    ]
    list_filter = [
        'status', 'exam_attended', 'booking_date', 'exam_date__exam_date',
        'exam_date__center__city', 'exam_date__center__country'
    ]
    search_fields = [
        'student__first_name', 'student__last_name', 'student__student_id',
        'exam_date__center__name', 'payment_reference'
    ]
    readonly_fields = [
        'id', 'booking_date', 'created_by', 'updated_by', 'created_at',
        'updated_at', 'amount_paid', 'payment_reference', 'payment_date'
    ]
    autocomplete_fields = [
        'student', 'exam_date', 'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Booking Information', {
            'fields': ('student', 'exam_date', 'status')
        }),
        ('Payment Information', {
            'fields': ('amount_paid', 'payment_reference', 'payment_date')
        }),
        ('Exam Day', {
            'fields': ('exam_attended', 'remarks')
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
            'student__user',  # For student name lookup
            'exam_date',
            'exam_date__center',
            'created_by',
            'updated_by'
        )