from django.db import models
import uuid
from django.utils import timezone
from django.core.validators import RegexValidator
from apps.students.models import Student
from apps.accounts.models import User
from apps.courses.models import Course, Class


class NotificationType(models.Model):
    """
    Types of notifications that can be sent.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text='Unique identifier for the notification type')
    display_name = models.CharField(max_length=200, help_text='Human-readable name')
    description = models.TextField(blank=True, help_text='Description of when this notification is sent')

    # Channels through which this notification can be sent
    can_send_email = models.BooleanField(default=True)
    can_send_sms = models.BooleanField(default=False)
    can_send_push = models.BooleanField(default=False)
    can_send_in_app = models.BooleanField(default=True)

    # Template fields
    email_subject_template = models.CharField(max_length=200, blank=True, help_text='Template for email subject')
    email_body_template = models.TextField(blank=True, help_text='Template for email body')
    sms_template = models.CharField(max_length=160, blank=True, help_text='Template for SMS (max 160 chars)')
    push_template = models.CharField(max_length=200, blank=True, help_text='Template for push notification')
    in_app_template = models.TextField(blank=True, help_text='Template for in-app notification')

    # Settings
    is_active = models.BooleanField(default=True, help_text='Whether this notification type is active')
    is_enabled_for_students = models.BooleanField(default=True, help_text='Whether students can receive this notification')
    is_enabled_for_staff = models.BooleanField(default=True, help_text='Whether staff can receive this notification')

    # Rate limiting (optional)
    cooldown_period_minutes = models.PositiveIntegerField(
        default=0,
        help_text='Minimum minutes between sending this notification type to the same recipient (0 = no limit)'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notification_types_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notification_types_updated')

    class Meta:
        db_table = 'notification_types'
        verbose_name = 'Notification Type'
        verbose_name_plural = 'Notification Types'
        ordering = ['display_name']

    def __str__(self):
        return self.display_name


class Notification(models.Model):
    """
    Individual notification records.
    """
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Who the notification is for
    recipient = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text='Student recipient (if applicable)'
    )
    recipient_staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='staff_notifications',
        null=True,
        blank=True,
        help_text='Staff recipient (if applicable)'
    )

    # What type of notification this is
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Delivery details
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')

    # Content
    subject = models.CharField(max_length=200, blank=True, help_text='Notification subject/title')
    body = models.TextField(help_text='Notification body/content')

    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True, help_text='When the notification was sent')
    delivered_at = models.DateTimeField(null=True, blank=True, help_text='When the notification was delivered')
    failed_at = models.DateTimeField(null=True, blank=True, help_text='When the notification failed')
    failure_reason = models.TextField(blank=True, help_text='Reason for failure if applicable')

    # Related objects (optional)
    related_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Related course (if applicable)'
    )
    related_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Related class (if applicable)'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_updated')

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        recipient_name = ""
        if self.recipient:
            recipient_name = self.recipient.get_full_name()
        elif self.recipient_staff:
            recipient_name = self.recipient_staff.get_full_name()
        return f"{self.notification_type.display_name} to {recipient_name} via {self.get_channel_display()}"

    @property
    def recipient_name(self):
        """Get the recipient's full name."""
        if self.recipient:
            return self.recipient.get_full_name()
        elif self.recipient_staff:
            return self.recipient_staff.get_full_name()
        return "Unknown"

    @property
    def is_sent(self):
        """Check if notification has been sent."""
        return self.status in ['sent', 'delivered']

    @property
    def is_failed(self):
        """Check if notification has failed."""
        return self.status == 'failed'

    @property
    def is_pending(self):
        """Check if notification is pending."""
        return self.status == 'pending'


class DeviceToken(models.Model):
    """
    Device tokens for push notifications.
    """
    DEVICE_TYPE_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Who this device belongs to
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='device_tokens'
    )
    # Device information
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPE_CHOICES)
    device_token = models.CharField(
        max_length=255,
        unique=True,
        help_text='Device token from push notification service'
    )
    device_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Human-readable device name (e.g., "John\'s iPhone")'
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='device_tokens_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='device_tokens_updated')

    class Meta:
        db_table = 'device_tokens'
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_device_type_display()} ({self.device_name or 'Unknown Device'})"

    class Meta:
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Tokens'


class NotificationTemplate(models.Model):
    """
    Templates for generating notifications dynamically.
    """
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    description = models.TextField(blank=True)

    # Template content
    subject_template = models.CharField(max_length=200, blank=True, help_text='Template for subject (email only)')
    body_template = models.TextField(help_text='Template for body/content')

    # Variables that can be used in template (documented in help_text)
    template_variables = models.TextField(
        blank=True,
        help_text='Comma-separated list of variable names available in template (e.g., student_name, course_name, exam_date)'
    )

    # Example data for preview
    example_data = models.TextField(
        blank=True,
        help_text='JSON example data for previewing the template'
    )

    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notification_templates_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notification_templates_updated')

    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    @property
    def variables_list(self):
        """Get template variables as a list."""
        if self.template_variables:
            return [var.strip() for var in self.template_variables.split(',') if var.strip()]
        return []