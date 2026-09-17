from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator


class CourseCategory(models.Model):
    """Category for grouping similar courses."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_categories'
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    """Course model representing what AUSSIZ offers."""
    COURSE_TYPES = [
        ('ielts', 'IELTS Preparation'),
        ('computer_package', 'Computer Package'),
        # Additional course types can be added here
    ]

    DELIVERY_MODE_CHOICES = [
        ('in_person', 'In-Person'),
        ('online', 'Online'),
        ('hybrid', 'Hybrid'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_code = models.CharField(max_length=20, unique=True, help_text='e.g., IELTS-001, COMP-001')
    name = models.CharField(max_length=200)
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField()
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES)
    duration_weeks = models.PositiveIntegerField(help_text='Duration in weeks')
    duration_hours = models.PositiveIntegerField(help_text='Total hours')
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_MODE_CHOICES, default='in_person')
    fee = models.DecimalField(max_digits=10, decimal_places=2, help_text='Course fee in KES')
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Registration fee in KES')
    minimum_students = models.PositiveIntegerField(default=1, help_text='Minimum students to run course')
    maximum_students = models.PositiveIntegerField(help_text='Maximum students allowed')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_created')
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_updated')

    class Meta:
        db_table = 'courses'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['name']

    def __str__(self):
        return f"{self.course_code} - {self.name}"

    def clean(self):
        """Validate course model."""
        if self.minimum_students > self.maximum_students:
            raise ValidationError({'minimum_students': 'Minimum students cannot be greater than maximum students.'})


class Class(models.Model):
    """Specific instance/session of a course being taught."""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=100, help_text='e.g., IELTS Morning Sep 2026')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='classes_created')
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='classes_updated')

    class Meta:
        db_table = 'classes'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.course.course_code} - {self.name} ({self.start_date})"

    def clean(self):
        """Validate class model."""
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError({'end_date': 'End date cannot be before start date.'})

    @property
    def duration_days(self):
        """Calculate duration in days."""
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None

    @property
    def student_count(self):
        """Get current number of enrolled students."""
        return self.enrollments.filter(is_active=True).count()

    @property
    def is_full(self):
        """Check if class is at maximum capacity."""
        return self.student_count >= self.course.maximum_students

    @property
    def available_spots(self):
        """Get number of available spots."""
        return max(0, self.course.maximum_students - self.student_count)