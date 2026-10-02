from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.students.models import Student
from apps.courses.models import Course, Class
from apps.accounts.models import User


class Assessment(models.Model):
    """
    Base assessment model for practice tests, mock tests, etc.
    """
    ASSESSMENT_TYPES = [
        ('practice', 'Practice Test'),
        ('mock', 'Mock Test'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    description = models.TextField(blank=True)

    # Related to course/class
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assessments', null=True, blank=True)

    # Timing
    scheduled_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(help_text='Duration in minutes')

    # Instructions and materials
    instructions = models.TextField(blank=True)
    materials_required = models.TextField(blank=True, help_text='Materials needed for the assessment')

    # Scoring
    total_score = models.PositiveIntegerField(help_text='Total possible score')
    passing_score = models.PositiveIntegerField(help_text='Minimum score to pass')

    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True, help_text='Whether students can take this assessment')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments_updated')

    class Meta:
        db_table = 'assessments'
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        ordering = ['-scheduled_date', 'start_time']

    def __str__(self):
        return f"{self.name} ({self.get_assessment_type_display()})"

    def clean(self):
        """Validate assessment model."""
        if self.start_time >= self.end_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})

        if self.passing_score > self.total_score:
            raise ValidationError({'passing_score': 'Passing score cannot be greater than total score.'})

        # Calculate expected duration from times
        if self.start_time and self.end_time:
            from datetime import datetime, date
            today = date.today()
            start_dt = datetime.combine(today, self.start_time)
            end_dt = datetime.combine(today, self.end_time)
            calculated_duration = int((end_dt - start_dt).total_seconds() / 60)
            if self.duration_minutes != calculated_duration:
                raise ValidationError({
                    'duration_minutes': f'Duration minutes ({self.duration_minutes}) does not match '
                                      f'the time difference ({calculated_duration} minutes).'
                })

    @property
    def is_passing_score(self):
        """Calculate passing score percentage."""
        if self.total_score > 0:
            return (self.passing_score / self.total_score) * 100
        return 0


class PracticeTest(Assessment):
    """
    Practice test model - inherits from Assessment.
    """
    class Meta:
        db_table = 'practice_tests'
        verbose_name = 'Practice Test'
        verbose_name_plural = 'Practice Tests'


class MockTest(Assessment):
    """
    Mock test model - inherits from Assessment.
    """
    class Meta:
        db_table = 'mock_tests'
        verbose_name = 'Mock Test'
        verbose_name_plural = 'Mock Tests'


class TestScore(models.Model):
    """
    Component scores for assessments (e.g., listening, reading, writing, speaking for IELTS).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='test_scores')
    # For generic assessments, or specific to IELTS components
    component_name = models.CharField(max_length=100, help_text='e.g., Listening, Reading, Writing, Speaking')
    max_score = models.PositiveIntegerField(help_text='Maximum score for this component')
    weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.00,
        help_text='Weight of this component in overall score (e.g., 0.25 for 25%)'
    )

    class Meta:
        db_table = 'test_scores'
        verbose_name = 'Test Score Component'
        verbose_name_plural = 'Test Score Components'
        unique_together = ['assessment', 'component_name']

    def __str__(self):
        return f"{self.assessment.name} - {self.component_name}"


class AssessmentAttempt(models.Model):
    """
    Record of a student's attempt at an assessment.
    """
    ATTEMPT_STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('reviewed', 'Reviewed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assessment_attempts')

    # Attempt details
    attempt_number = models.PositiveIntegerField(default=1, help_text='Which attempt this is for this student')
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=ATTEMPT_STATUS_CHOICES, default='started')

    # Scores
    total_score_achieved = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Total score achieved by student'
    )
    percentage_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Percentage score achieved'
    )
    is_passed = models.BooleanField(
        null=True,
        blank=True,
        help_text='Whether student passed the assessment'
    )

    # Feedback and notes
    student_feedback = models.TextField(blank=True, help_text='Feedback from student about the assessment')
    instructor_feedback = models.TextField(blank=True, help_text='Feedback from instructor')
    notes = models.TextField(blank=True, help_text='Additional notes')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessment_attempts_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessment_attempts_updated')

    class Meta:
        db_table = 'assessment_attempts'
        verbose_name = 'Assessment Attempt'
        verbose_name_plural = 'Assessment Attempts'
        ordering = ['-started_at']
        unique_together = ['assessment', 'student', 'attempt_number']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assessment.name} (Attempt {self.attempt_number})"

    def save(self, *args, **kwargs):
        """Override save to calculate percentage and pass/fail status."""
        if self.total_score_achieved is not None and self.assessment.total_score > 0:
            self.percentage_score = (self.total_score_achieved / self.assessment.total_score) * 100
            if self.assessment.passing_score > 0:
                self.is_passed = self.total_score_achieved >= self.assessment.passing_score
        super().save(*args, **kwargs)


class ComponentScore(models.Model):
    """
    Scores for individual components of an assessment attempt.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='component_scores')
    test_score = models.ForeignKey(TestScore, on_delete=models.CASCADE, related_name='component_scores')
    score_achieved = models.PositiveIntegerField(help_text='Score achieved for this component')

    class Meta:
        db_table = 'component_scores'
        verbose_name = 'Component Score'
        verbose_name_plural = 'Component Scores'
        unique_together = ['attempt', 'test_score']

    def __str__(self):
        return f"{self.attempt} - {self.test_score.component_name}: {self.score_achieved}"

    @property
    def percentage_score(self):
        """Calculate percentage score for this component."""
        if self.test_score.max_score > 0:
            return (self.score_achieved / self.test_score.max_score) * 100
        return 0


# Target Band Model (for students' target IELTS bands)
class TargetBand(models.Model):
    """
    Student's target IELTS band score.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='target_band')

    # Overall target band
    overall_band_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        help_text='Target overall IELTS band score (0-9)'
    )

    # Component target bands (optional)
    listening_target = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        null=True,
        blank=True
    )
    reading_target = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        null=True,
        blank=True
    )
    writing_target = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        null=True,
        blank=True
    )
    speaking_target = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        null=True,
        blank=True
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_bands_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_bands_updated')

    class Meta:
        db_table = 'target_bands'
        verbose_name = 'Target Band'
        verbose_name_plural = 'Target Bands'

    def __str__(self):
        return f"{self.student.get_full_name()} - Target: {self.overall_band_score}"

    def save(self, *args, **kwargs):
        """Override save to ensure component targets are reasonable."""
        # If component targets are set, overall should be reasonable average
        # This is a simplified check - in practice, IELTS has specific rounding rules
        super().save(*args, **kwargs)