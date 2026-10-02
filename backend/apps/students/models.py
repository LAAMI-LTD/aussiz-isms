from django.db import models
import uuid
from django.core.validators import RegexValidator
from apps.accounts.models import User
from django.utils import timezone
import re


class NextOfKin(models.Model):
    """Model for student's next of kin/emergency contact."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='next_of_kin_entries', blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')]
    )
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'next_of_kin'
        verbose_name = 'Next of Kin'
        verbose_name_plural = 'Next of Kin'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship})"


class StudentDocument(models.Model):
    """Model for storing student documents."""
    DOCUMENT_TYPES = [
        ('id_passport', 'ID/Passport'),
        ('passport_photo', 'Passport Photo'),
        ('admission_form', 'Admission Form'),
        ('ielts_result', 'IELTS Result'),
        ('supporting_doc', 'Supporting Document'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='student_documents/%Y/%m/%d/')
    file_size = models.PositiveIntegerField(help_text='File size in bytes')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'student_documents'
        verbose_name = 'Student Document'
        verbose_name_plural = 'Student Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.get_document_type_display()}"


class Student(models.Model):
    """Core student model."""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    NATIONALITY_CHOICES = [
        ('KE', 'Kenyan'),
        ('UG', 'Ugandan'),
        ('TZ', 'Tanzanian'),
        ('ET', 'Ethiopian'),
        ('SO', 'Somali'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deferred', 'Deferred'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
        ('inactive', 'Inactive'),
    ]

    ENGLISH_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('elementary', 'Elementary'),
        ('pre_intermediate', 'Pre-Intermediate'),
        ('intermediate', 'Intermediate'),
        ('upper_intermediate', 'Upper Intermediate'),
        ('advanced', 'Advanced'),
        ('proficiency', 'Proficiency'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Student ID will be generated like SAKE/SEP/26/01
    student_id = models.CharField(max_length=20, unique=True, blank=True)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=10, choices=NATIONALITY_CHOICES, default='KE')
    national_id_passport = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')]
    )
    email = models.EmailField()
    address = models.TextField()

    # Next of Kin relationship is handled via NextOfKin model's foreign key to Student

    # Academic Information
    previous_education = models.TextField(blank=True)
    english_level = models.CharField(max_length=20, choices=ENGLISH_LEVEL_CHOICES, blank=True)
    previous_ielts_attempts = models.PositiveIntegerField(default=0)
    intended_destination = models.CharField(max_length=100, blank=True)

    # Status & Timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='students_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='students_updated')

    # Photo
    photo = models.ImageField(upload_to='student_photos/%Y/%m/%d/', blank=True, null=True)

    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.student_id} - {self.get_full_name()}"

    def get_full_name(self):
        """Return the student's full name."""
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        """Override save to generate student ID if not set."""
        if not self.student_id:
            self.student_id = self.generate_student_id()
        super().save(*args, **kwargs)

    def generate_student_id(self):
        """
        Generate student ID in format: SAKE/SEP/26/01
        Where:
        - SAKE: Fixed prefix for AUSSIZ
        - SEP: Month abbreviation (3 letters)
        - 26: Year (2 digits)
        - 01: Sequential number (2 digits, reset yearly)
        """
        from datetime import datetime
        from django.db.models import Max

        now = timezone.now()
        year = now.strftime('%y')  # 2-digit year (e.g., '26' for 2026)
        month = now.strftime('%b').upper()  # 3-letter month uppercase (e.g., 'SEP')

        # Find the latest student ID for this month/year
        prefix = f"SAKE/{month}/{year}/"
        latest_id = Student.objects.filter(
            student_id__startswith=prefix
        ).aggregate(
            max_id=Max('student_id')
        )['max_id']

        if latest_id:
            # Extract the sequence number and increment
            try:
                # Handle case where student_id might not match expected format
                match = re.search(r'/(\d+)$', latest_id)
                if match:
                    sequence = int(match.group(1)) + 1
                else:
                    sequence = 1
            except (ValueError, IndexError, AttributeError):
                sequence = 1
        else:
            sequence = 1

        # Format sequence as 2-digit number
        sequence_str = f"{sequence:02d}"

        return f"{prefix}{sequence_str}"