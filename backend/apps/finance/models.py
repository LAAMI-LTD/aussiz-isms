from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest, IELTSTestAttempt
from apps.bookings.models import IELTSExamBooking


class FeeType(models.Model):
    """Defines different types of fees that can be charged."""
    FEE_CATEGORIES = [
        ('tuition', 'Tuition'),
        ('registration', 'Registration'),
        ('exam', 'Exam Fee'),
        ('materials', 'Study Materials'),
        ('late', 'Late Fee'),
        ('discount', 'Discount'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text='Name of the fee type')
    category = models.CharField(max_length=20, choices=FEE_CATEGORIES)
    description = models.TextField(blank=True)
    # Default amount (can be overridden in FeeItem)
    default_amount = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Default amount for this fee type'
    )
    # Whether this fee is taxable
    is_taxable = models.BooleanField(default=False)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.0,
        help_text='Tax rate as decimal (e.g., 0.10 for 10%)'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fee_types_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fee_types_updated'
    )

    class Meta:
        db_table = 'finance_fee_types'
        verbose_name = 'Fee Type'
        verbose_name_plural = 'Fee Types'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class FeeItem(models.Model):
    """Represents a specific fee that can be charged to a student."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # What the fee is for
    fee_type = models.ForeignKey(
        FeeType, on_delete=models.CASCADE, related_name='fee_items'
    )
    # Optional links to specific entities
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, null=True, blank=True,
        related_name='fee_items'
    )
    ielts_test = models.ForeignKey(
        IELTSTest, on_delete=models.CASCADE, null=True, blank=True,
        related_name='fee_items'
    )
    ielts_attempt = models.ForeignKey(
        IELTSTestAttempt, on_delete=models.CASCADE, null=True, blank=True,
        related_name='fee_items'
    )
    exam_booking = models.ForeignKey(
        IELTSExamBooking, on_delete=models.CASCADE, null=True, blank=True,
        related_name='fee_items'
    )
    # Fee details
    description = models.CharField(max_length=200, help_text='Description of the fee')
    amount = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Fee amount'
    )
    # Dates
    due_date = models.DateField(help_text='Date when fee is due')
    # Discount information
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text='Discount percentage (0-100)'
    )
    # Status
    is_paid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fee_items_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fee_items_updated'
    )

    class Meta:
        db_table = 'finance_fee_items'
        verbose_name = 'Fee Item'
        verbose_name_plural = 'Fee Items'
        ordering = ['due_date']

    def __str__(self):
        return f"{self.fee_type.name} - {self.description} (${self.amount})"

    def clean(self):
        """Validate fee item data."""
        # Ensure at least one entity is linked if not a general fee
        if not any([self.student, self.ielts_test, self.ielts_attempt, self.exam_booking]):
            # General fees (like registration) might not need a specific entity
            pass

        # Validate discount percentage
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValidationError({
                'discount_percentage': 'Discount percentage must be between 0 and 100.'
            })

    @property
    def discounted_amount(self):
        """Calculate amount after discount."""
        if self.discount_percentage > 0:
            discount_amount = self.amount * (self.discount_percentage / 100)
            return self.amount - discount_amount
        return self.amount

    @property
    def is_overdue(self):
        """Check if fee is overdue."""
        return not self.is_paid and timezone.now().date() > self.due_date


class Invoice(models.Model):
    """Represents an invoice sent to a student."""
    INVOICE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Invoice identification
    invoice_number = models.CharField(
        max_length=50, unique=True, help_text='Unique invoice identifier'
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='invoices'
    )
    # Invoice details
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(help_text='Date when invoice is due')
    status = models.CharField(
        max_length=20, choices=INVOICE_STATUS_CHOICES, default='draft'
    )
    # Financial information
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Subtotal before taxes'
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        default=0.0,
        help_text='Tax amount'
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Total amount due'
    )
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        default=0.0,
        help_text='Amount paid so far'
    )
    # Notes
    notes = models.TextField(blank=True, help_text='Additional notes or terms')
    # Audit fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices_updated'
    )

    class Meta:
        db_table = 'finance_invoices'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-issue_date']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.student.get_full_name()}"

    def clean(self):
        """Validate invoice data."""
        # Ensure due date is not before issue date
        if self.due_date < self.issue_date:
            raise ValidationError({
                'due_date': 'Due date cannot be before issue date.'
            })

        # Ensure amount paid doesn't exceed total amount
        if self.amount_paid > self.total_amount:
            raise ValidationError({
                'amount_paid': 'Amount paid cannot exceed total amount.'
            })

    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not provided
        if not self.invoice_number:
            # Format: INV-YYYYMMDD-XXXX
            date_str = timezone.now().strftime('%Y%m%d')
            # Get the latest invoice number for today to avoid duplicates
            latest_today = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{date_str}-'
            ).order_by('-invoice_number').first()

            if latest_today:
                # Extract the sequence number and increment
                try:
                    last_seq = int(latest_today.invoice_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1

            self.invoice_number = f'INV-{date_str}-{new_seq:04d}'

        # Calculate total amount before saving
        if self.pk is None:  # Only calculate on creation
            self.total_amount = self.subtotal + self.tax_amount

        self.clean()
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        """Calculate remaining balance due."""
        return max(0, self.total_amount - self.amount_paid)

    @property
    def is_fully_paid(self):
        """Check if invoice is fully paid."""
        return self.amount_paid >= self.total_amount

    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        return (self.status not in ['paid', 'cancelled'] and
                timezone.now().date() > self.due_date and
                self.balance_due > 0)

    def update_status(self):
        """Update invoice status based on payment and dates."""
        if self.is_fully_paid:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partially_paid'
        elif self.is_overdue:
            self.status = 'overdue'
        else:
            self.status = 'sent'


class InvoiceItem(models.Model):
    """Represents a line item on an invoice."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='items'
    )
    # What the item is for
    fee_item = models.ForeignKey(
        FeeItem, on_delete=models.CASCADE, null=True, blank=True,
        related_name='invoice_items'
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
        db_table = 'finance_invoice_items'
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
        ordering = ['id']

    def __str__(self):
        return f"{self.description} × {self.quantity} @ ${self.unit_price}"

    def clean(self):
        """Validate invoice item data."""
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


class Payment(models.Model):
    """Represents a payment made by a student."""
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('online', 'Online Payment'),
        ('other', 'Other'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Payment identification
    payment_number = models.CharField(
        max_length=50, unique=True, help_text='Unique payment identifier'
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='payments'
    )
    # What the payment is for
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, null=True, blank=True,
        related_name='payments'
    )
    # Payment details
    payment_date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Payment amount'
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES
    )
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending'
    )
    # Transaction information
    transaction_id = models.CharField(
        max_length=100, blank=True, help_text='Transaction ID from payment gateway'
    )
    # Notes
    notes = models.TextField(blank=True, help_text='Additional notes about the payment')
    # Audit fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payments_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payments_updated'
    )

    class Meta:
        db_table = 'finance_payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.payment_number} - ${self.amount} ({self.get_payment_method_display()})"

    def clean(self):
        """Validate payment data."""
        # Ensure amount is positive
        if self.amount <= 0:
            raise ValidationError({
                'amount': 'Payment amount must be greater than zero.'
            })

        # If linked to invoice, ensure payment doesn't exceed invoice balance
        if self.invoice and self.amount > self.invoice.balance_due:
            raise ValidationError({
                'amount': f'Payment amount cannot exceed invoice balance due (${self.invoice.balance_due}).'
            })

    def save(self, *args, **kwargs):
        # Auto-generate payment number if not provided
        if not self.payment_number:
            # Format: PAY-YYYYMMDD-XXXX
            date_str = timezone.now().strftime('%Y%m%d')
            # Get the latest payment number for today to avoid duplicates
            latest_today = Payment.objects.filter(
                payment_number__startswith=f'PAY-{date_str}-'
            ).order_by('-payment_number').first()

            if latest_today:
                # Extract the sequence number and increment
                try:
                    last_seq = int(latest_today.payment_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1

            self.payment_number = f'PAY-{date_str}-{new_seq:04d}'

        self.clean()
        super().save(*args, **kwargs)

    def mark_as_processed(self, transaction_id=None):
        """Mark payment as processed."""
        self.status = 'processed'
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

        # Update invoice if linked
        if self.invoice:
            self.invoice.amount_paid += self.amount
            self.invoice.update_status()
            self.invoice.save(update_fields=['amount_paid', 'status'])

    def mark_as_failed(self):
        """Mark payment as failed."""
        self.status = 'failed'
        self.save()

    def refund(self):
        """Refund the payment."""
        if self.status != 'processed':
            raise ValidationError({
                'status': 'Only processed payments can be refunded.'
            })

        self.status = 'refunded'
        self.save()

        # Update invoice if linked
        if self.invoice:
            self.invoice.amount_paid -= self.amount
            self.invoice.update_status()
            self.invoice.save(update_fields=['amount_paid', 'status'])


class Receipt(models.Model):
    """Represents a receipt issued for a payment."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Receipt identification
    receipt_number = models.CharField(
        max_length=50, unique=True, help_text='Unique receipt identifier'
    )
    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name='receipt'
    )
    # Receipt details
    issue_date = models.DateTimeField(default=timezone.now)
    # Amounts
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text='Receipt amount'
    )
    # Notes
    notes = models.TextField(blank=True, help_text='Additional notes')
    # Audit fields
    is_active = models.BooleanField(default=True)
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
        db_table = 'finance_receipts'
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        ordering = ['-issue_date']

    def __str__(self):
        return f"Receipt {self.receipt_number} - Payment {self.payment.payment_number}"

    def clean(self):
        """Validate receipt data."""
        # Ensure receipt amount matches payment amount
        if self.amount != self.payment.amount:
            raise ValidationError({
                'amount': 'Receipt amount must match payment amount.'
            })

    def save(self, *args, **kwargs):
        # Auto-generate receipt number if not provided
        if not self.receipt_number:
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

            self.receipt_number = f'REC-{date_str}-{new_seq:04d}'

        # Ensure amount matches payment
        if self.payment:
            self.amount = self.payment.amount

        self.clean()
        super().save(*args, **kwargs)