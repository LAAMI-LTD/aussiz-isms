from django.contrib import admin
from .models import Student, NextOfKin, StudentDocument


class NextOfKinInline(admin.StackedInline):
    model = NextOfKin
    extra = 0


class StudentDocumentInline(admin.StackedInline):
    model = StudentDocument
    extra = 0
    readonly_fields = ('uploaded_at', 'file_size')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'gender', 'nationality', 'status', 'date_created')
    list_filter = ('gender', 'nationality', 'status', 'date_created')
    search_fields = ('student_id', 'first_name', 'last_name', 'national_id_passport', 'email')
    readonly_fields = ('student_id', 'date_created', 'date_updated')
    inlines = [NextOfKinInline, StudentDocumentInline]

    fieldsets = (
        ('Student ID', {
            'fields': ('student_id',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'gender', 'date_of_birth', 'nationality', 'national_id_passport', 'phone_number', 'email', 'address', 'photo')
        }),
        ('Academic Information', {
            'fields': ('previous_education', 'english_level', 'previous_ielts_attempts', 'target_band', 'intended_destination')
        }),
                ('Status & Timestamps', {
            'fields': ('status', 'date_created', 'date_updated', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(NextOfKin)
class NextOfKinAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'relationship', 'phone_number')
    search_fields = ('first_name', 'last_name', 'phone_number')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('student', 'document_type', 'title', 'uploaded_by', 'uploaded_at', 'is_verified')
    list_filter = ('document_type', 'is_verified', 'uploaded_at')
    search_fields = ('student__first_name', 'student__last_name', 'title')
    readonly_fields = ('uploaded_at', 'file_size')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'uploaded_by', 'verified_by')