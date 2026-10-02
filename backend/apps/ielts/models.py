from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.students.models import Student
from apps.accounts.models import User


class IELTSTest(models.Model):
    """Represents an IELTS practice or mock test."""
    TEST_TYPES = [
        ('practice', 'Practice Test'),
        ('mock', 'Mock Test'),
        ('official', 'Official Test'),
    ]

    TEST_MODES = [
        ('academic', 'Academic'),
        ('general_training', 'General Training'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, help_text='e.g., IELTS Practice Test 1')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    test_mode = models.CharField(max_length=20, choices=TEST_MODES)
    description = models.TextField(blank=True)
    # For practice/mock tests, we might have a reference to the source material
    source_material = models.CharField(max_length=200, blank=True, help_text='Source book/material')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_tests_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_tests_updated')

    class Meta:
        db_table = 'ielts_tests'
        verbose_name = 'IELTS Test'
        verbose_name_plural = 'IELTS Tests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.test_type.title()} - {self.title}"


class IELTSTestSection(models.Model):
    """Represents a section of an IELTS test (Listening, Reading, Writing, Speaking)."""
    SECTION_TYPES = [
        ('listening', 'Listening'),
        ('reading', 'Reading'),
        ('writing', 'Writing'),
        ('speaking', 'Speaking'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(IELTSTest, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    # Order of sections in the test (Listening=1, Reading=2, Writing=3, Speaking=4)
    order = models.PositiveIntegerField()
    # Time limit for this section in minutes
    time_limit_minutes = models.PositiveIntegerField(help_text='Time limit in minutes')
    # Total marks available for this section
    total_marks = models.PositiveIntegerField(help_text='Total marks available')
    instructions = models.TextField(blank=True, help_text='Instructions for this section')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ielts_test_sections'
        verbose_name = 'IELTS Test Section'
        verbose_name_plural = 'IELTS Test Sections'
        ordering = ['test', 'order']
        unique_together = ['test', 'section_type']  # Each section type appears once per test

    def __str__(self):
        return f"{self.test.title} - {self.get_section_type_display()}"


class IELTSTestAttempt(models.Model):
    """Represents a student's attempt at an IELTS test."""
    ATTEMPT_STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('reviewed', 'Reviewed by Tutor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='ielts_attempts')
    test = models.ForeignKey(IELTSTest, on_delete=models.CASCADE, related_name='attempts')
    # When the attempt was started
    started_at = models.DateTimeField(auto_now_add=True)
    # When the attempt was completed/completed
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ATTEMPT_STATUS_CHOICES, default='in_progress')
    # Overall band score (calculated from section scores)
    overall_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Overall IELTS band score (0-9)'
    )
    # Notes from tutor or student
    remarks = models.TextField(blank=True)
    # Who reviewed the attempt (if applicable)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_attempts_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_attempts_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_attempts_updated')

    class Meta:
        db_table = 'ielts_test_attempts'
        verbose_name = 'IELTS Test Attempt'
        verbose_name_plural = 'IELTS Test Attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.test.title} ({self.started_at.strftime('%Y-%m-%d')})"

    def clean(self):
        """Validate the test attempt."""
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValidationError({'completed_at': 'Completion date cannot be before start date.'})

        if self.overall_band_score is not None:
            if self.overall_band_score < 0.0 or self.overall_band_score > 9.0:
                raise ValidationError({'overall_band_score': 'Overall band score must be between 0 and 9.'})


class IELTSTestSectionScore(models.Model):
    """Represents a student's score for a specific section of an IELTS test attempt."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(IELTSTestAttempt, on_delete=models.CASCADE, related_name='section_scores')
    section = models.ForeignKey(IELTSTestSection, on_delete=models.CASCADE, related_name='attempt_scores')
    # Raw score obtained (out of total_marks for the section)
    raw_score = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text='Raw score obtained in this section'
    )
    # Converted band score (0-9 scale, can include .5 increments)
    band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='IELTS band score for this section (0-9)'
    )
    # Percentage score
    percentage_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Percentage score for this section'
    )
    # Whether the answers have been reviewed
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_section_scores_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, help_text='Teacher remarks or feedback')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ielts_test_section_scores'
        verbose_name = 'IELTS Test Section Score'
        verbose_name_plural = 'IELTS Test Section Scores'
        ordering = ['attempt', 'section__order']
        unique_together = ['attempt', 'section']  # One score per section per attempt

    def __str__(self):
        return f"{self.attempt.student.get_full_name()} - {self.section.get_section_type_display()}: {self.band_score}"

    def clean(self):
        """Validate the section score."""
        # Validate raw score doesn't exceed section total marks
        if self.section and self.raw_score > self.section.total_marks:
            raise ValidationError({
                'raw_score': f'Raw score cannot exceed total marks ({self.section.total_marks}) for this section.'
            })

        # Validate band score is within valid range
        if self.band_score < 0.0 or self.band_score > 9.0:
            raise ValidationError({
                'band_score': 'Band score must be between 0 and 9.'
            })

        # Validate percentage score is within valid range
        if self.percentage_score < 0.0 or self.percentage_score > 100.0:
            raise ValidationError({
                'percentage_score': 'Percentage score must be between 0 and 100.'
            })


class IELTSProgress(models.Model):
    """Tracks a student's IELTS progress over time."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='ielts_progress')
    # Target band score the student is aiming for
    target_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Target IELTS band score (0-9)'
    )
    # Current estimated band score based on recent attempts
    current_estimated_band = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Current estimated band score based on recent performance'
    )
    # Date when the target was set or last updated
    target_date = models.DateField()
    # Last assessment date
    last_assessment_date = models.DateField(null=True, blank=True)
    # Notes on progress, strengths, weaknesses
    progress_notes = models.TextField(blank=True)
    # Recommended focus areas
    recommended_focus = models.TextField(blank=True, help_text='Areas to focus on for improvement')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_progress_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ielts_progress_updated')

    class Meta:
        db_table = 'ielts_progress'
        verbose_name = 'IELTS Progress'
        verbose_name_plural = 'IELTS Progress'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - IELTS Progress"

    def clean(self):
        """Validate the progress record."""
        if self.target_band_score < 0.0 or self.target_band_score > 9.0:
            raise ValidationError({
                'target_band_score': 'Target band score must be between 0 and 9.'
            })

        if self.current_estimated_band is not None:
            if self.current_estimated_band < 0.0 or self.current_estimated_band > 9.0:
                raise ValidationError({
                    'current_estimated_band': 'Current estimated band must be between 0 and 9.'
                })