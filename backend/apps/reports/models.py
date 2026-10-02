from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.students.models import Student
from apps.accounts.models import User
from apps.courses.models import Course, Class
from apps.attendance.models import AttendanceSession, AttendanceRecord
from apps.finance.models import Payment, Invoice
from apps.assessments.models import Assessment, AssessmentAttempt
from apps.ielts.models import IELTSTest, IELTSTestAttempt


class ReportCategory(models.Model):
    """
    Categories for grouping different types of reports.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Icon for UI representation
    icon = models.CharField(max_length=50, blank=True, help_text='CSS class or icon name')
    color = models.CharField(max_length=7, blank=True, help_text='Hex color code (e.g., #3B82F6)')
    is_active = models.BooleanField(default=True)
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_categories_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_categories_updated')

    class Meta:
        db_table = 'report_categories'
        verbose_name = 'Report Category'
        verbose_name_plural = 'Report Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class ReportTemplate(models.Model):
    """
    Templates for generating reports.
    """
    REPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]

    REPORT_TYPES = [
        # Management Reports
        ('management_summary', 'Management Summary'),
        ('financial_overview', 'Financial Overview'),
        ('student_enrollment', 'Student Enrollment'),
        ('staff_performance', 'Staff Performance'),

        # Academic Reports
        ('course_completion', 'Course Completion'),
        ('assessment_results', 'Assessment Results'),
        ('curriculum_coverage', 'Curriculum Coverage'),
        ('progress_tracking', 'Progress Tracking'),

        # Attendance Reports
        ('attendance_summary', 'Attendance Summary'),
        ('attendance_trends', 'Attendance Trends'),
        ('absenteeism_report', 'Absenteeism Report'),
        ('punctuality_report', 'Punctuality Report'),

        # Finance Reports
        ('revenue_report', 'Revenue Report'),
        ('outstanding_payments', 'Outstanding Payments'),
        ('fee_collection', 'Fee Collection'),
        ('financial_audit', 'Financial Audit'),

        # IELTS Performance Reports
        ('ielts_performance', 'IELTS Performance'),
        ('component_analysis', 'Component Analysis'),
        ('band_score_distribution', 'Band Score Distribution'),
        ('improvement_tracking', 'Improvement Tracking'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    category = models.ForeignKey(ReportCategory, on_delete=models.CASCADE, related_name='report_templates')
    description = models.TextField(blank=True)

    # Template configuration
    format = models.CharField(max_length=20, choices=REPORT_FORMATS, default='pdf')
    is_active = models.BooleanField(default=True)
    is_scheduled = models.BooleanField(default=False, help_text='Whether this report can be scheduled for automatic generation')

    # Parameters that can be customized when generating the report
    parameters_schema = models.JSONField(
        blank=True, null=True,
        help_text='JSON schema defining parameters for report generation (e.g., date ranges, filters)'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_templates_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_templates_updated')

    class Meta:
        db_table = 'report_templates'
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class GeneratedReport(models.Model):
    """
    Instances of generated reports.
    """
    REPORT_STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Related to template
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='generated_reports')

    # Report identification
    report_number = models.CharField(
        max_length=50, unique=True, help_text='Unique report identifier'
    )
    name = models.CharField(max_length=200, help_text='Custom name for this report instance')
    description = models.TextField(blank=True)

    # Generation details
    status = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default='generating')
    format = models.CharField(max_length=20, choices=ReportTemplate.REPORT_FORMATS)
    parameters = models.JSONField(
        default=dict, blank=True,
        help_text='Parameters used for generating this report'
    )

    # File outputs
    file = models.FileField(
        upload_to='reports/%Y/%m/%d/',
        null=True, blank=True,
        help_text='Generated report file'
    )
    file_size = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Size of the generated file in bytes'
    )

    # Timing
    generated_at = models.DateTimeField(null=True, blank=True)
    generation_started_at = models.DateTimeField(null=True, blank=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)

    # Audit fields
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_updated')

    class Meta:
        db_table = 'generated_reports'
        verbose_name = 'Generated Report'
        verbose_name_plural = 'Generated Reports'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.name} ({self.report_number})"

    def clean(self):
        """Validate generated report data."""
        # Ensure report number follows expected format if not auto-generated
        if self.report_number and not self.report_number.startswith('REP-'):
            # Allow manually set report numbers but warn
            pass

    def save(self, *args, **kwargs):
        # Auto-generate report number if not provided
        if not self.report_number:
            self.report_number = self.generate_report_number()

        # Set format from template if not explicitly set
        if not self.format and self.template:
            self.format = self.template.format

        self.clean()
        super().save(*args, **kwargs)

    def generate_report_number(self):
        """Generate a unique report number."""
        # Format: REP-YYYYMMDD-XXXX
        date_str = timezone.now().strftime('%Y%m%d')

        # Get the latest report number for today to avoid duplicates
        latest_today = GeneratedReport.objects.filter(
            report_number__startswith=f'REP-{date_str}-'
        ).order_by('-report_number').first()

        if latest_today:
            # Extract the sequence number and increment
            try:
                last_seq = int(latest_today.report_number.split('-')[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        return f'REP-{date_str}-{new_seq:04d}'

    @property
    def is_ready(self):
        """Check if report is ready for download."""
        return self.status == 'completed' and bool(self.file)

    @property
    def generation_duration(self):
        """Calculate generation duration in seconds."""
        if self.generation_started_at and self.generation_completed_at:
            return (self.generation_completed_at - self.generation_started_at).total_seconds()
        return None

    def mark_as_generating(self):
        """Mark report as currently being generated."""
        self.status = 'generating'
        self.generation_started_at = timezone.now()
        self.save(update_fields=['status', 'generation_started_at'])

    def mark_as_completed(self, file_path=None, file_size=None):
        """Mark report as completed."""
        self.status = 'completed'
        self.generation_completed_at = timezone.now()
        if file_path:
            self.file = file_path
        if file_size is not None:
            self.file_size = file_size
        self.save(update_fields=['status', 'generation_completed_at', 'file', 'file_size'])

    def mark_as_failed(self, error_message=None):
        """Mark report as failed."""
        self.status = 'failed'
        self.generation_completed_at = timezone.now()
        # In a real implementation, you might want to store the error message
        self.save(update_fields=['status', 'generation_completed_at'])


class ReportSchedule(models.Model):
    """
    Schedule for automatic report generation.
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Related to template
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='schedules')

    # Schedule details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    # For weekly reports: 0=Monday, 6=Sunday
    day_of_week = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text='Day of week for weekly reports (0=Monday, 6=Sunday)'
    )
    # For monthly reports: 1-31
    day_of_month = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Day of month for monthly reports'
    )
    # Time of day
    time_of_day = models.TimeField(help_text='Time of day to generate the report')

    # Parameters for report generation
    parameters = models.JSONField(
        default=dict, blank=True,
        help_text='Default parameters for scheduled report generation'
    )

    # Status
    is_active = models.BooleanField(default=True)
    last_generated_at = models.DateTimeField(null=True, blank=True)
    next_generation_at = models.DateTimeField(null=True, blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_schedules_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_schedules_updated')

    class Meta:
        db_table = 'report_schedules'
        verbose_name = 'Report Schedule'
        verbose_name_plural = 'Report Schedules'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

    def clean(self):
        """Validate schedule data."""
        # Validate day_of_week for weekly frequency
        if self.frequency == 'weekly' and self.day_of_week is None:
            raise ValidationError({
                'day_of_week': 'Day of week is required for weekly reports.'
            })
        elif self.frequency != 'weekly' and self.day_of_week is not None:
            raise ValidationError({
                'day_of_week': 'Day of week is only applicable for weekly reports.'
            })

        # Validate day_of_month for monthly frequency
        if self.frequency == 'monthly' and self.day_of_month is None:
            raise ValidationError({
                'day_of_month': 'Day of month is required for monthly reports.'
            })
        elif self.frequency != 'monthly' and self.day_of_month is not None:
            raise ValidationError({
                'day_of_month': 'Day of month is only applicable for monthly reports.'
            })

    def save(self, *args, **kwargs):
        self.clean()
        # Calculate next generation time
        if self.is_active:
            self.next_generation_at = self.calculate_next_generation()
        else:
            self.next_generation_at = None
        super().save(*args, **kwargs)

    def calculate_next_generation(self):
        """Calculate the next generation time based on frequency."""
        now = timezone.now()
        if self.frequency == 'daily':
            # Next occurrence at the same time today or tomorrow
            next_gen = now.replace(
                hour=self.time_of_day.hour,
                minute=self.time_of_day.minute,
                second=self.time_of_day.second,
                microsecond=0
            )
            if next_gen <= now:
                next_gen += timezone.timedelta(days=1)
            return next_gen
        elif self.frequency == 'weekly':
            # Next occurrence on the specified day of week
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_gen = now.replace(
                hour=self.time_of_day.hour,
                minute=self.time_of_day.minute,
                second=self.time_of_day.second,
                microsecond=0
            ) + timezone.timedelta(days=days_ahead)
            return next_gen
        elif self.frequency == 'monthly':
            # Next occurrence on the specified day of month
            if now.day < self.day_of_month:
                # This month
                next_gen = now.replace(
                    day=self.day_of_month,
                    hour=self.time_of_day.hour,
                    minute=self.time_of_day.minute,
                    second=self.time_of_day.second,
                    microsecond=0
                )
            else:
                # Next month
                if now.month == 12:
                    next_gen = now.replace(
                        year=now.year + 1,
                        month=1,
                        day=self.day_of_month,
                        hour=self.time_of_day.hour,
                        minute=self.time_of_day.minute,
                        second=self.time_of_day.second,
                        microsecond=0
                    )
                else:
                    next_gen = now.replace(
                        month=now.month + 1,
                        day=self.day_of_month,
                        hour=self.time_of_day.hour,
                        minute=self.time_of_day.minute,
                        second=self.time_of_day.second,
                        microsecond=0
                    )
            # If the calculated time has already passed this month, go to next occurrence
            if next_gen <= now:
                # Add approximately one month
                if next_gen.month == 12:
                    next_gen = next_gen.replace(
                        year=next_gen.year + 1,
                        month=1
                    )
                else:
                    next_gen = next_gen.replace(
                        month=next_gen.month + 1
                    )
            return next_gen
        elif self.frequency == 'quarterly':
            # Every 3 months
            months_to_add = 3
            next_gen = now
            while True:
                # Try to set to the target day of month
                try:
                    if next_gen.month + months_to_add > 12:
                        next_gen = next_gen.replace(
                            year=next_gen.year + (next_gen.month + months_to_add - 1) // 12,
                            month=(next_gen.month + months_to_add - 1) % 12 + 1,
                            day=self.day_of_month,
                            hour=self.time_of_day.hour,
                            minute=self.time_of_day.minute,
                            second=self.time_of_day.second,
                            microsecond=0
                        )
                    else:
                        next_gen = next_gen.replace(
                            month=next_gen.month + months_to_add,
                            day=self.day_of_month,
                            hour=self.time_of_day.hour,
                            minute=self.time_of_day.minute,
                            second=self.time_of_day.second,
                            microsecond=0
                        )
                except ValueError:
                    # Day doesn't exist in that month, use last day of month
                    if next_gen.month + months_to_add > 12:
                        next_gen = next_gen.replace(
                            year=next_gen.year + (next_gen.month + months_to_add - 1) // 12,
                            month=(next_gen.month + months_to_add - 1) % 12 + 1,
                            day=28,  # Conservative estimate
                            hour=self.time_of_day.hour,
                            minute=self.time_of_day.minute,
                            second=self.time_of_day.second,
                            microsecond=0
                        )
                    else:
                        next_gen = next_gen.replace(
                            month=next_gen.month + months_to_add,
                            day=28,  # Conservative estimate
                            hour=self.time_of_day.hour,
                            minute=self.time_of_day.minute,
                            second=self.time_of_day.second,
                            microsecond=0
                        )
                if next_gen > now:
                    break
                # Try next quarter
                months_to_add += 3
            return next_gen
        elif self.frequency == 'yearly':
            # Next occurrence on the specified day of month next year
            try:
                next_gen = now.replace(
                    year=now.year + 1,
                    month=now.month,
                    day=self.day_of_month,
                    hour=self.time_of_day.hour,
                    minute=self.time_of_day.minute,
                    second=self.time_of_day.second,
                    microsecond=0
                )
            except ValueError:
                # Handle Feb 29 on non-leap years
                next_gen = now.replace(
                    year=now.year + 1,
                    month=2,
                    day=28,
                    hour=self.time_of_day.hour,
                    minute=self.time_of_day.minute,
                    second=self.time_of_day.second,
                    microsecond=0
                )
            if next_gen <= now:
                next_gen = next_gen.replace(year=next_gen.year + 1)
            return next_gen
        return None