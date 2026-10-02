from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest, IELTSTestAttempt


class IELTSResult(models.Model):
    """Stores official IELTS test results."""
    RESULT_STATUS_CHOICES = [
        ('pending', 'Pending Release'),
        ('released', 'Released'),
        ('under_review', 'Under Review'),
        ('withheld', 'Withheld'),
        ('cancelled', 'Cancelled'),
    ]

    RESULT_FORMAT_CHOICES = [
        ('electronic', 'Electronic'),
        ('paper', 'Paper'),
        ('both', 'Both Electronic and Paper'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to the student's attempt
    attempt = models.OneToOneField(
        IELTSTestAttempt, on_delete=models.CASCADE, related_name='official_result'
    )
    # Alternative: direct links if attempt is not always available
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='ielts_results'
    )
    test = models.ForeignKey(
        IELTSTest, on_delete=models.CASCADE, related_name='official_results'
    )

    # Individual section band scores (0-9 scale)
    listening_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Listening band score'
    )
    reading_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Reading band score'
    )
    writing_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Writing band score'
    )
    speaking_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Speaking band score'
    )

    # Overall band score (calculated from section scores)
    overall_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Overall IELTS band score (0-9)'
    )

    # Result information
    result_status = models.CharField(
        max_length=20, choices=RESULT_STATUS_CHOICES, default='pending'
    )
    result_format = models.CharField(
        max_length=20, choices=RESULT_FORMAT_CHOICES, default='electronic'
    )
    result_id = models.CharField(
        max_length=50, unique=True, help_text='Unique result identifier for verification'
    )
    release_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateField(
        help_text='Date when result expires (typically 2 years from test date)'
    )

    # Verification information
    is_verified = models.BooleanField(
        default=False, help_text='Whether the result has been verified by an external party'
    )
    verification_count = models.PositiveIntegerField(
        default=0, help_text='Number of times this result has been verified'
    )
    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verified_results'
    )

    # Remarks and notes
    remarks = models.TextField(
        blank=True, help_text='Administrator remarks or special notes'
    )

    # Audit fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='results_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='results_updated'
    )

    class Meta:
        db_table = 'ielts_results'
        verbose_name = 'IELTS Result'
        verbose_name_plural = 'IELTS Results'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.test.title} ({self.overall_band_score})"

    def clean(self):
        """Validate the result data."""
        # Validate that overall band score is the average of section scores
        section_scores = [
            self.listening_band_score,
            self.reading_band_score,
            self.writing_band_score,
            self.speaking_band_score
        ]

        # Calculate expected overall band score (average of 4 sections, rounded to nearest 0.5)
        if all(score is not None for score in section_scores):
            average_band = sum(section_scores) / len(section_scores)
            expected_overall = round(average_band * 2) / 2

            # Allow small tolerance for rounding differences
            if abs(self.overall_band_score - expected_overall) > 0.1:
                raise ValidationError({
                    'overall_band_score': f'Overall band score should be {expected_overall} '
                                        f'(average of section scores).'
                })

        # Validate expiry date is reasonable (typically 2 years from test date)
        if self.expiry_date and self.release_date:
            # This is a simplified check - in reality, expiry is usually 2 years from test date
            pass

        # Ensure result ID is unique
        if IELTSResult.objects.filter(result_id=self.result_id).exclude(
            pk=self.pk if self.pk else None
        ).exists():
            raise ValidationError({
                'result_id': 'A result with this ID already exists.'
            })

    def save(self, *args, **kwargs):
        # Auto-calculate overall band score if not provided
        if self.overall_band_score is None:
            section_scores = [
                self.listening_band_score,
                self.reading_band_score,
                self.writing_band_score,
                self.speaking_band_score
            ]
            if all(score is not None for score in section_scores):
                average_band = sum(section_scores) / len(section_scores)
                self.overall_band_score = round(average_band * 2) / 2
                # Ensure within bounds
                self.overall_band_score = max(0.0, min(9.0, self.overall_band_score))

        # Set release date if status is being changed to released
        if self.result_status == 'released' and not self.release_date:
            self.release_date = timezone.now()

        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if the result has expired."""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def years_until_expiry(self):
        """Get years until result expires."""
        if self.expiry_date:
            from datetime import date
            delta = self.expiry_date - timezone.now().date()
            return max(0, delta.days / 365.25)
        return None


class IELTSResultVerification(models.Model):
    """Tracks verification requests for IELTS results."""
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Verification Failed'),
        ('expired', 'Result Expired'),
    ]

    VERIFICATION_TYPE_CHOICES = [
        ('institution', 'Educational Institution'),
        ('employer', 'Employer'),
        ('government', 'Government Agency'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.ForeignKey(
        IELTSResult, on_delete=models.CASCADE, related_name='verifications'
    )
    # Requestor information
    requestor_name = models.CharField(max_length=200)
    requestor_institution = models.CharField(max_length=200)
    requestor_email = models.EmailField()
    requestor_phone = models.CharField(max_length=20, blank=True)
    verification_type = models.CharField(
        max_length=20, choices=VERIFICATION_TYPE_CHOICES
    )
    # Verification details
    verification_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending'
    )
    verification_reference = models.CharField(
        max_length=100, blank=True, help_text='Reference ID from requesting organization'
    )
    # Results shared (what information was provided)
    shared_overall_score = models.BooleanField(default=True)
    shared_section_scores = models.BooleanField(default=True)
    shared_personal_details = models.BooleanField(default=False)
    # Remarks
    remarks = models.TextField(blank=True)
    # Audit fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verification_requests_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verification_requests_updated'
    )

    class Meta:
        db_table = 'ielts_result_verifications'
        verbose_name = 'IELTS Result Verification'
        verbose_name_plural = 'IELTS Result Verifications'
        ordering = ['-verification_date']

    def __str__(self):
        return f"Verification for {self.result.result_id} by {self.requestor_name}"

    def clean(self):
        """Validate verification request data."""
        # Check if result is released and not expired
        if self.result.result_status != 'released':
            raise ValidationError({
                'result': 'Can only verify released results.'
            })

        if self.result.is_expired:
            raise ValidationError({
                'result': 'Cannot verify expired results.'
            })

    def save(self, *args, **kwargs):
        self.clean()
        # Update verification count on result when a new verification is created
        if not self.pk:  # New verification
            super().save(*args, **kwargs)
            # Update the result's verification count and timestamp
            self.result.verification_count += 1
            self.result.last_verified_at = timezone.now()
            self.result.last_verified_by = self.created_by
            self.result.is_verified = True
            self.result.save(update_fields=[
                'verification_count', 'last_verified_at',
                'last_verified_by', 'is_verified'
            ])
        else:
            super().save(*args, **kwargs)


class IELTSResultAudit(models.Model):
    """Audit trail for changes to IELTS results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.ForeignKey(
        IELTSResult, on_delete=models.CASCADE, related_name='audit_trail'
    )
    # What changed
    field_name = models.CharField(max_length=100, help_text='Name of the field that changed')
    old_value = models.TextField(blank=True, help_text='Previous value (as string)')
    new_value = models.TextField(blank=True, help_text='New value (as string)')
    # Change information
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='result_audits'
    )
    change_reason = models.CharField(
        max_length=200, blank=True, help_text='Reason for the change'
    )
    # IP address and user agent for security tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'ielts_result_audit'
        verbose_name = 'IELTS Result Audit'
        verbose_name_plural = 'IELTS Result Audits'
        ordering = ['-changed_at']

    def __str__(self):
        return f"Audit for {self.result.result_id}: {self.field_name} changed"