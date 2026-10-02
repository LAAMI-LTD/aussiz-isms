from django.contrib import admin
from .models import FeeType, FeeItem, Invoice, InvoiceItem, Payment, Receipt
from apps.students.models import Student
from apps.accounts.models import User


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'default_amount', 'is_taxable',
        'tax_rate', 'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'is_active', 'is_taxable', 'created_at'
    ]
    search_fields = [
        'name', 'description'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['created_by', 'updated_by']

    fieldsets = (
        ('Fee Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Amount & Tax', {
            'fields': ('default_amount', 'is_taxable', 'tax_rate')
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


@admin.register(FeeItem)
class FeeItemAdmin(admin.ModelAdmin):
    list_display = [
        'fee_type', 'student', 'description', 'amount',
        'discount_percentage', 'discounted_amount', 'due_date',
        'is_paid', 'is_active', 'is_overdue'
    ]
    list_filter = [
        'is_paid', 'is_active', 'is_overdue', 'due_date',
        'fee_type__category', 'fee_type__is_taxable'
    ]
    search_fields = [
        'description',
        'student__first_name', 'student__last_name', 'student__student_id',
        'fee_type__name'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'discounted_amount', 'is_overdue'
    ]
    autocomplete_fields = [
        'fee_type', 'student', 'ielts_test', 'ielts_attempt',
        'exam_booking', 'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Fee Information', {
            'fields': ('fee_type', 'description')
        }),
        ('Related Entities', {
            'fields': ('student', 'ielts_test', 'ielts_attempt', 'exam_booking'),
            'classes': ('collapse',)
        }),
        ('Amount & Dates', {
            'fields': ('amount', 'discount_percentage', 'due_date')
        }),
        ('Calculated Fields', {
            'fields': ('discounted_amount', 'is_overdue')
        }),
        ('Status', {
            'fields': ('is_paid', 'is_active')
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
            'fee_type',
            'student',
            'student__user',
            'ielts_test',
            'ielts_attempt',
            'exam_booking',
            'exam_booking__student',
            'created_by',
            'updated_by'
        )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'student', 'issue_date', 'due_date',
        'status', 'subtotal', 'tax_amount', 'total_amount',
        'amount_paid', 'balance_due', 'is_overdue'
    ]
    list_filter = [
        'status', 'is_active', 'issue_date', 'due_date'
    ]
    search_fields = [
        'invoice_number',
        'student__first_name', 'student__last_name', 'student__student_id',
        'notes'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'invoice_number', 'subtotal', 'tax_amount', 'total_amount',
        'amount_paid', 'balance_due', 'is_fully_paid', 'is_overdue'
    ]
    autocomplete_fields = [
        'student', 'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'student')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax_amount', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('amount_paid', 'balance_due', 'is_fully_paid')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes', 'is_overdue')
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
            'student',
            'student__user',
            'created_by',
            'updated_by'
        ).prefetch_related('items__fee_item__fee_type')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'invoice', 'description', 'quantity', 'unit_price',
        'line_total', 'is_taxable', 'tax_rate', 'tax_amount'
    ]
    list_filter = [
        'is_taxable', 'invoice__status'
    ]
    search_fields = [
        'description',
        'invoice__invoice_number',
        'invoice__student__first_name',
        'invoice__student__last_name'
    ]
    readonly_fields = [
        'id', 'line_total', 'tax_amount'
    ]
    autocomplete_fields = [
        'invoice', 'fee_item', 'fee_item__fee_type'
    ]

    fieldsets = (
        ('Item Information', {
            'fields': ('invoice', 'description')
        }),
        ('Quantity & Pricing', {
            'fields': ('quantity', 'unit_price', 'line_total')
        }),
        ('Tax Information', {
            'fields': ('is_taxable', 'tax_rate', 'tax_amount')
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related(
            'invoice',
            'invoice__student',
            'fee_item',
            'fee_item__fee_type'
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number', 'student', 'amount', 'payment_method',
        'status', 'payment_date', 'transaction_id'
    ]
    list_filter = [
        'status', 'payment_method', 'payment_date'
    ]
    search_fields = [
        'payment_number',
        'student__first_name', 'student__last_name', 'student__student_id',
        'transaction_id', 'notes'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'payment_number'
    ]
    autocomplete_fields = [
        'student', 'invoice', 'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_number', 'student', 'invoice')
        }),
        ('Amount & Method', {
            'fields': ('amount', 'payment_method')
        }),
        ('Status & Transaction', {
            'fields': ('status', 'transaction_id')
        }),
        ('Date & Notes', {
            'fields': ('payment_date', 'notes')
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
            'student',
            'student__user',
            'invoice',
            'invoice__student',
            'created_by',
            'updated_by'
        )


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'payment', 'payment__student',
        'amount', 'issue_date'
    ]
    list_filter = [
        'issue_date'
    ]
    search_fields = [
        'receipt_number',
        'payment__payment_number',
        'payment__student__first_name',
        'payment__student__last_name',
        'payment__student__student_id'
    ]
    readonly_fields = [
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'receipt_number', 'amount'
    ]
    autocomplete_fields = [
        'payment', 'payment__student', 'created_by', 'updated_by'
    ]

    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_number', 'payment')
        }),
        ('Amount & Date', {
            'fields': ('amount', 'issue_date')
        }),
        ('Notes', {
            'fields': ('notes',)
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
            'payment',
            'payment__student',
            'payment__student__user',
            'created_by',
            'updated_by'
        )