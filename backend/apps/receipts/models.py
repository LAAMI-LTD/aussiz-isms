from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.students.models import Student
from apps.accounts.models import User
from apps.finance.models import Payment, Invoice


class Receipt(models.Model):
    """
    Model for representing receipts issued for payments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Receipt identification
    receipt_number = models.CharField(
        max_length=50, unique=True, help_text='Unique receipt identifier'
    )

    # Related to payment and invoice
    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name='receipt'
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='receipts'
    )

    # Receipt details
    issue_date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Receipt amount'
    )

    # Additional information
    notes = models.TextField(blank=True, help_text='Additional notes')
    terms_and_conditions = models.TextField(
        blank=True, help_text='Terms and conditions for the receipt'
    )

    # PDF generation
    pdf_file = models.FileField(
        upload_to='receipts/pdfs/%Y/%m/%d/',
        null=True, blank=True,
        help_text='PDF version of the receipt'
    )
    pdf_generated_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(
        default=False, help_text='Whether receipt has been cancelled'
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cancelled_receipts'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='receipts_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='receipts_updated'
    )

    class Meta:
        db_table = 'receipts_receipt'
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        ordering = ['-issue_date']

    def __str__(self):
        return f"Receipt {self.receipt_number} - Payment {self.payment.payment_number}"

    def clean(self):
        """Validate receipt data."""
        # Ensure receipt amount matches payment amount
        if self.payment and self.amount != self.payment.amount:
            raise ValidationError({
                'amount': 'Receipt amount must match payment amount.'
            })

        # Ensure invoice is related to payment if provided
        if self.invoice and self.payment and self.invoice != self.payment.invoice:
            raise ValidationError({
                'invoice': 'Invoice must be related to the payment.'
            })

    def save(self, *args, **kwargs):
        # Auto-generate receipt number if not provided
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()

        # Ensure amount matches payment
        if self.payment:
            self.amount = self.payment.amount

        self.clean()
        super().save(*args, **kwargs)

    def generate_receipt_number(self):
        """Generate a unique receipt number."""
        # Format: REC-YYYYMMDD-XXXX
        date_str = timezone.now().strftime('%Y%m%d')

        # Get the latest receipt number for today to avoid duplicates
        latest_today = Receipt.objects.filter(
            receipt_number__startswith=f'REC-{date_str}-'
        ).order_by('-receipt_number').first()

        if latest_today:
            # Extract the sequence number and increment
            try:
                last_seq = int(latest_today.receipt_number.split('-')[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        return f'REC-{date_str}-{new_seq:04d}'

    def generate_pdf(self):
        """Generate PDF version of the receipt."""
        # This would typically use a library like WeasyReport or ReportLab
        # For now, we'll just mark that PDF generation is needed
        # In a real implementation, this would generate and save the PDF file
        self.pdf_generated_at = timezone.now()
        self.save(update_fields=['pdf_generated_at'])
        return self.pdf_file

    def cancel(self, cancelled_by_user=None):
        """Cancel the receipt."""
        self.is_cancelled = True
        self.cancelled_at = timezone.now()
        if cancelled_by_user:
            self.cancelled_by = cancelled_by_user
        self.is_active = False
        self.save()

    @property
    def is_pdf_available(self):
        """Check if PDF is available for download."""
        return bool(self.pdf_file and self.pdf_generated_at)


class ReceiptItem(models.Model):
    """
    Model for representing line items on a receipt.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name='items'
    )

    # Item details
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Price per unit'
    )

    # Calculated fields
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Total for this line item (quantity × unit price)'
    )

    # Tax information
    is_taxable = models.BooleanField(default=False)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.0,
        help_text='Tax rate as decimal'
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        default=0.0,
        help_text='Tax amount for this line item'
    )

    class Meta:
        db_table = 'receipts_receipt_item'
        verbose_name = 'Receipt Item'
        verbose_name_plural = 'Receipt Items'
        ordering = ['id']

    def __str__(self):
        return f"{self.description} × {self.quantity} @ ${self.unit_price}"

    def clean(self):
        """Validate receipt item data."""
        # Ensure quantities and prices are positive
        if self.quantity <= 0:
            raise ValidationError({
                'quantity': 'Quantity must be greater than zero.'
            })

        if self.unit_price < 0:
            raise ValidationError({
                'unit_price': 'Unit price cannot be negative.'
            })

    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.quantity * self.unit_price

        # Calculate tax amount
        if self.is_taxable:
            self.tax_amount = self.line_total * self.tax_rate
        else:
            self.tax_amount = 0

        self.clean()
        super().save(*args, **kwargs)


class ReceiptHistory(models.Model):
    """
    Model for tracking changes to receipts for audit purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name='history_entries'
    )

    # Change details
    changed_at = models.DateTimeField(default=timezone.now)
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='receipt_changes'
    )
    change_description = models.CharField(
        max_length=200, help_text='Description of what changed'
    )

    # Store snapshot of key fields at time of change
    receipt_number_snapshot = models.CharField(max_length=50)
    amount_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date_snapshot = models.DateTimeField()
    is_cancelled_snapshot = models.BooleanField(default=False)

    # Additional context
    change_reason = models.TextField(
        blank=True, help_text='Reason for the change'
    )

    class Meta:
        db_table = 'receipts_receipt_history'
        verbose_name = 'Receipt History'
        verbose_name_plural = 'Receipt History'
        ordering = ['-changed_at']

    def __str__(self):
        return f"History for {self.receipt_number} at {self.changed_at}"

    def save(self, *args, **kwargs):
        # Auto-populate snapshot fields if not provided
        if self.receipt and not self.receipt_number_snapshot:
            self.receipt_number_snapshot = self.receipt.receipt_number
            self.amount_snapshot = self.receipt.amount
            self.issue_date_snapshot = self.receipt.issue_date
            self.is_cancelled_snapshot = self.receipt.is_cancelled

        super().save(*args, **kwargs)