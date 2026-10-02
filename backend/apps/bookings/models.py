from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest


class IELTSExamCenter(models.Model):
    """Represents an IELTS exam center where tests are conducted."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text='Name of the exam center')
    address = models.TextField(help_text='Full address of the exam center')
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    # Capacity information
    daily_capacity = models.PositiveIntegerField(
        help_text='Maximum number of exams that can be conducted per day'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exam_centers_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exam_centers_updated'
    )

    class Meta:
        db_table = 'ielts_exam_centers'
        verbose_name = 'IELTS Exam Center'
        verbose_name_plural = 'IELTS Exam Centers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.city}, {self.country}"


class IELTSExamDate(models.Model):
    """Represents a specific date when an IELTS exam is offered at a center."""
    EXAM_TYPES = [
        ('academic', 'Academic'),
        ('general_training', 'General Training'),
        ('both', 'Both Academic and General Training'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(
        IELTSExamCenter, on_delete=models.CASCADE, related_name='exam_dates'
    )
    exam_type = models.CharField(
        max_length=20, choices=EXAM_TYPES,
        help_text='Type of IELTS exam offered on this date'
    )
    exam_date = models.DateField(help_text='Date when the exam is conducted')
    registration_deadline = models.DateField(
        help_text='Last date for registration for this exam date'
    )
    # Capacity information
    total_slots = models.PositiveIntegerField(
        help_text='Total number of slots available for this exam date'
    )
    filled_slots = models.PositiveIntegerField(
        default=0, help_text='Number of slots already filled'
    )
    available_slots = models.PositiveIntegerField(
        default=0, help_text='Number of slots still available'
    )
    # Fee information
    exam_fee = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text='Exam fee in local currency'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exam_dates_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exam_dates_updated'
    )

    class Meta:
        db_table = 'ielts_exam_dates'
        verbose_name = 'IELTS Exam Date'
        verbose_name_plural = 'IELTS Exam Dates'
        ordering = ['exam_date']
        unique_together = ['center', 'exam_date']  # One exam date per center per day

    def __str__(self):
        return f"{self.center.name} - {self.exam_date} ({self.get_exam_type_display()})"

    def clean(self):
        """Validate the exam date."""
        if self.registration_deadline > self.exam_date:
            raise ValidationError({
                'registration_deadline': 'Registration deadline cannot be after the exam date.'
            })

        if self.filled_slots > self.total_slots:
            raise ValidationError({
                'filled_slots': 'Filled slots cannot exceed total slots.'
            })

        # Calculate available slots
        self.available_slots = max(0, self.total_slots - self.filled_slots)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class IELTSExamBooking(models.Model):
    """Represents a student's booking for an IELTS exam."""
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='ielts_exam_bookings'
    )
    exam_date = models.ForeignKey(
        IELTSExamDate, on_delete=models.CASCADE, related_name='bookings'
    )
    # Booking information
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending'
    )
    # Payment information (will be linked to finance phase)
    amount_paid = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00,
        help_text='Amount paid so far'
    )
    payment_reference = models.CharField(
        max_length=100, blank=True,
        help_text='Reference ID from payment gateway'
    )
    payment_date = models.DateTimeField(null=True, blank=True)
    # Exam day information
    exam_attended = models.BooleanField(
        default=False, help_text='Whether the student attended the exam'
    )
    # Notes and remarks
    remarks = models.TextField(blank=True, help_text='Administrator notes')
    # Audit fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exam_bookings_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exam_bookings_updated'
    )

    class Meta:
        db_table = 'ielts_exam_bookings'
        verbose_name = 'IELTS Exam Booking'
        verbose_name_plural = 'IELTS Exam Bookings'
        ordering = ['-booking_date']
        unique_together = ['student', 'exam_date']  # One booking per student per exam date

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exam_date} ({self.status})"

    def clean(self):
        """Validate the exam booking."""
        # Check if exam date is still available for booking
        if self.exam_date.available_slots <= 0 and self.status not in ['cancelled', 'completed']:
            raise ValidationError({
                'exam_date': 'No available slots for this exam date.'
            })

        # Check if registration deadline has passed
        if timezone.now().date() > self.exam_date.registration_deadline and self.status == 'pending':
            raise ValidationError({
                'exam_date': 'Registration deadline has passed for this exam date.'
            })

    def save(self, *args, **kwargs):
        # Update filled slots when booking is confirmed
        if self.status == 'confirmed' and self.pk is None:
            # New confirmed booking
            self.exam_date.filled_slots += 1
            self.exam_date.save()
        elif self.status == 'cancelled' and self.pk is not None:
            # Booking was cancelled
            try:
                old_booking = IELTSExamBooking.objects.get(pk=self.pk)
                if old_booking.status == 'confirmed' and self.status != 'confirmed':
                    # Changed from confirmed to cancelled
                    self.exam_date.filled_slots = max(0, self.exam_date.filled_slots - 1)
                    self.exam_date.save()
            except IELTSExamBooking.DoesNotExist:
                pass  # New booking

        self.clean()
        super().save(*args, **kwargs)