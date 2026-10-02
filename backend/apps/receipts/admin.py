from django.contrib import admin
from .models import Receipt, ReceiptItem, ReceiptHistory
from apps.finance.models import Payment, Invoice
from apps.students.models import Student
from apps.accounts.models import User


class ReceiptItemInline(admin.TabularInline):
    """
    Inline for displaying receipt items in the receipt admin.
    """
    model = ReceiptItem
    extra = 0
    readonly_fields = ['line_total', 'tax_amount']


class ReceiptHistoryInline(admin.TabularInline):
    """
    Inline for displaying receipt history in the receipt admin.
    """
    model = ReceiptHistory
    extra = 0
    readonly_fields = ['changed_at', 'changed_by', 'change_description']


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'payment', 'invoice', 'issue_date',
        'amount', 'is_active', 'is_cancelled', 'pdf_generated_at'
    ]
    list_filter = [
        'is_active', 'is_cancelled', 'issue_date', 'pdf_generated_at',
        'created_at'
    ]
    search_fields = [
        'receipt_number', 'notes', 'payment__payment_number',
        'invoice__invoice_number'
    ]
    readonly_fields = [
        'id', 'receipt_number', 'issue_date', 'created_at', 'updated_at',
        'created_by', 'updated_by', 'pdf_generated_at'
    ]
    autocomplete_fields = [
        'payment', 'invoice', 'created_by', 'updated_by', 'cancelled_by'
    ]
    inlines = [ReceiptItemInline, ReceiptHistoryInline]

    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_number', 'payment', 'invoice')
        }),
        ('Receipt Details', {
            'fields': ('issue_date', 'amount', 'notes', 'terms_and_conditions')
        }),
        ('PDF Generation', {
            'fields': ('pdf_file', 'pdf_generated_at')
        }),
        ('Status', {
            'fields': ('is_active', 'is_cancelled', 'cancelled_at', 'cancelled_by')
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
            'payment', 'invoice', 'created_by', 'updated_by', 'cancelled_by'
        )


@admin.register(ReceiptItem)
class ReceiptItemAdmin(admin.ModelAdmin):
    list_display = [
        'receipt', 'description', 'quantity', 'unit_price',
        'line_total', 'is_taxable', 'tax_amount'
    ]
    list_filter = [
        'is_taxable', 'receipt__issue_date'
    ]
    search_fields = [
        'description', 'receipt__receipt_number'
    ]
    readonly_fields = [
        'id', 'line_total', 'tax_amount'
    ]
    autocomplete_fields = ['receipt']

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related('receipt')


@admin.register(ReceiptHistory)
class ReceiptHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'receipt', 'changed_at', 'changed_by', 'change_description',
        'amount_snapshot'
    ]
    list_filter = [
        'changed_at', 'changed_by'
    ]
    search_fields = [
        'receipt__receipt_number', 'change_description', 'change_reason'
    ]
    readonly_fields = [
        'id', 'receipt_number_snapshot', 'amount_snapshot',
        'issue_date_snapshot', 'is_cancelled_snapshot'
    ]
    autocomplete_fields = ['receipt', 'changed_by']

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related(
            'receipt', 'changed_by'
        )