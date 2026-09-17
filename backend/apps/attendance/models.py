from django.db import models
import uuid
from apps.students.models import Student
from apps.courses.models import Class
from apps.accounts.models import User


class AttendanceSession(models.Model):
    """Represents a specific class session for attendance tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_sessions')
    session_date = models.DateField()
    session_number = models.PositiveIntegerField(help_text='Session number within the class (1, 2, 3, etc.)')
    topic = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_sessions_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_sessions_updated')

    class Meta:
        db_table = 'attendance_sessions'
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'
        ordering = ['-session_date', 'session_number']
        unique_together = ['class_instance', 'session_date', 'session_number']

    def __str__(self):
        return f"{self.class_instance} - Session {self.session_number} ({self.session_date})"

    @property
    def duration_hours(self):
        """Calculate session duration in hours."""
        if self.start_time and self.end_time:
            from datetime import datetime
            start = datetime.combine(datetime.min, self.start_time)
            end = datetime.combine(datetime.min, self.end_time)
            duration = end - start
            return duration.total_seconds() / 3600
        return None


class AttendanceStatus(models.Model):
    """Different attendance status options."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)  # e.g., 'P', 'A', 'L', 'E'
    name = models.CharField(max_length=50)  # e.g., 'Present', 'Absent', 'Late', 'Excused'
    description = models.TextField(blank=True)
    is_present = models.BooleanField(default=False, help_text='Whether this status counts as present for reporting')
    points = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, help_text='Points awarded for this status (e.g., 1.0 for present, 0.5 for late)')
    color = models.CharField(max_length=7, default='#6B7280', help_text='Hex color for UI display')  # Default gray
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_statuses'
        verbose_name = 'Attendance Status'
        verbose_name_plural = 'Attendance Statuses'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class AttendanceRecord(models.Model):
    """Individual student attendance record for a session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.ForeignKey(AttendanceStatus, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records_recorded')
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_records'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = ['session', 'student']  # One record per student per session
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.session} - {self.status.name}"

    def save(self, *args, **kwargs):
        """Override save to ensure recorded_by is set if not provided."""
        if not self.recorded_by and hasattr(self, '_request_user'):
            self.recorded_by = self._request_user
        super().save(*args, **kwargs)