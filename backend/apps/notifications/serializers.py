from rest_framework import serializers
from .models import NotificationType, Notification, DeviceToken, NotificationTemplate
from apps.students.models import Student
from apps.accounts.models import User
from apps.courses.models import Course, Class
from apps.accounts.serializers import UserSerializer
from apps.students.serializers import StudentSerializer
from apps.courses.serializers import CourseSerializer, ClassSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model (nested)."""
    class Meta:
        model = Student
        fields = ['id', 'student_id', 'first_name', 'last_name']
        read_only_fields = fields


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model (nested)."""
    class Meta:
        model = Course
        fields = ['id', 'course_code', 'name']
        read_only_fields = fields


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class model (nested)."""
    class Meta:
        model = Class
        fields = ['id', 'name']
        read_only_fields = fields


class NotificationTypeSerializer(serializers.ModelSerializer):
    """Serializer for NotificationType model."""
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = NotificationType
        fields = [
            'id', 'name', 'display_name', 'description',
            'can_send_email', 'can_send_sms', 'can_send_push', 'can_send_in_app',
            'email_subject_template', 'email_body_template', 'sms_template',
            'push_template', 'in_app_template',
            'is_active', 'is_enabled_for_students', 'is_enabled_for_staff',
            'cooldown_period_minutes',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    recipient = StudentSerializer(read_only=True)
    recipient_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    recipient_staff = UserSerializer(read_only=True)
    recipient_staff_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    notification_type = NotificationTypeSerializer(read_only=True)
    notification_type_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    related_course = CourseSerializer(read_only=True)
    related_course_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    related_class = ClassSerializer(read_only=True)
    related_class_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    # Computed properties
    recipient_name = serializers.SerializerMethodField()
    is_sent = serializers.SerializerMethodField()
    is_failed = serializers.SerializerMethodField()
    is_pending = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_id', 'recipient_staff', 'recipient_staff_id',
            'notification_type', 'notification_type_id',
            'channel', 'status',
            'subject', 'body',
            'sent_at', 'delivered_at', 'failed_at', 'failure_reason',
            'related_course', 'related_course_id', 'related_class', 'related_class_id',
            'created_by', 'updated_by', 'created_at', 'updated_at',
            'recipient_name', 'is_sent', 'is_failed', 'is_pending'
        ]
        read_only_fields = [
            'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
            'sent_at', 'delivered_at', 'failed_at', 'recipient_name',
            'is_sent', 'is_failed', 'is_pending'
        ]

    def get_recipient_name(self, obj):
        """Get recipient's full name."""
        return obj.recipient_name

    def get_is_sent(self, obj):
        """Check if notification has been sent."""
        return obj.is_sent

    def get_is_failed(self, obj):
        """Check if notification has failed."""
        return obj.is_failed

    def get_is_pending(self, obj):
        """Check if notification is pending."""
        return obj.is_pending

    def validate(self, attrs):
        """Validate notification data."""
        recipient_id = attrs.get('recipient_id')
        recipient_staff_id = attrs.get('recipient_staff_id')
        notification_type_id = attrs.get('notification_type_id')
        channel = attrs.get('channel')
        subject = attrs.get('subject', '')
        body = attrs.get('body', '')

        # Ensure exactly one recipient type is specified
        if recipient_id and recipient_staff_id:
            raise serializers.ValidationError({
                'non_field_errors': 'Specify either recipient (student) or recipient_staff (staff), not both.'
            })
        if not recipient_id and not recipient_staff_id:
            raise serializers.ValidationError({
                'non_field_errors': 'Specify either recipient (student) or recipient_staff (staff).'
            })

        # Check if notification type exists
        if notification_type_id:
            try:
                NotificationType.objects.get(id=notification_type_id)
            except NotificationType.DoesNotExist:
                raise serializers.ValidationError({
                    'notification_type_id': 'Notification type does not exist.'
                })

        # Validate channel
        valid_channels = [choice[0] for choice in Notification.CHANNEL_CHOICES]
        if channel not in valid_channels:
            raise serializers.ValidationError({
                'channel': f'Invalid channel. Must be one of {valid_channels}.'
            })

        # Validate that the notification type supports this channel
        if notification_type_id:
            try:
                notification_type = NotificationType.objects.get(id=notification_type_id)
                if channel == 'email' and not notification_type.can_send_email:
                    raise serializers.ValidationError({
                        'channel': 'This notification type does not support email.'
                    })
                elif channel == 'sms' and not notification_type.can_send_sms:
                    raise serializers.ValidationError({
                        'channel': 'This notification type does not support SMS.'
                    })
                elif channel == 'push' and not notification_type.can_send_push:
                    raise serializers.ValidationError({
                        'channel': 'This notification type does not support push notifications.'
                    })
                elif channel == 'in_app' and not notification_type.can_send_in_app:
                    raise serializers.ValidationError({
                        'channel': 'This notification type does not support in-app notifications.'
                    })
            except NotificationType.DoesNotExist:
                pass  # Will be caught above

        # Validate content
        if not subject and not body:
            raise serializers.ValidationError({
                'non_field_errors': 'Either subject or body must be provided.'
            })

        # Validate SMS length if applicable
        if channel == 'sms' and body and len(body) > 160:
            raise serializers.ValidationError({
                'body': 'SMS messages cannot exceed 160 characters.'
            })

        # Validate related objects if provided
        related_course_id = attrs.get('related_course_id')
        related_class_id = attrs.get('related_class_id')

        if related_course_id:
            try:
                Course.objects.get(id=related_course_id)
            except Course.DoesNotExist:
                raise serializers.ValidationError({
                    'related_course_id': 'Course does not exist.'
                })

        if related_class_id:
            try:
                Class.objects.get(id=related_class_id)
            except Class.DoesNotExist:
                raise serializers.ValidationError({
                    'related_class_id': 'Class does not exist.'
                })

        return attrs

    def create(self, validated_data):
        """Create and return a new notification."""
        recipient_id = validated_data.pop('recipient_id', None)
        recipient_staff_id = validated_data.pop('recipient_staff_id', None)
        notification_type_id = validated_data.pop('notification_type_id')
        related_course_id = validated_data.pop('related_course_id', None)
        related_class_id = validated_data.pop('related_class_id', None)

        if recipient_id:
            validated_data['recipient'] = Student.objects.get(id=recipient_id)
        if recipient_staff_id:
            validated_data['recipient_staff'] = User.objects.get(id=recipient_staff_id)
        validated_data['notification_type'] = NotificationType.objects.get(id=notification_type_id)
        if related_course_id:
            validated_data['related_course'] = Course.objects.get(id=related_course_id)
        if related_class_id:
            validated_data['related_class'] = Class.objects.get(id=related_class_id)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update and return an existing notification."""
        recipient_id = validated_data.pop('recipient_id', None)
        recipient_staff_id = validated_data.pop('recipient_staff_id', None)
        notification_type_id = validated_data.pop('notification_type_id', None)
        related_course_id = validated_data.pop('related_course_id', None)
        related_class_id = validated_data.pop('related_class_id', None)

        if recipient_id is not None:
            if recipient_id:
                validated_data['recipient'] = Student.objects.get(id=recipient_id)
            else:
                validated_data['recipient'] = None
        if recipient_staff_id is not None:
            if recipient_staff_id:
                validated_data['recipient_staff'] = User.objects.get(id=recipient_staff_id)
            else:
                validated_data['recipient_staff'] = None
        if notification_type_id is not None:
            validated_data['notification_type'] = NotificationType.objects.get(id=notification_type_id)
        if related_course_id is not None:
            if related_course_id:
                validated_data['related_course'] = Course.objects.get(id=related_course_id)
            else:
                validated_data['related_course'] = None
        if related_class_id is not None:
            if related_class_id:
                validated_data['related_class'] = Class.objects.get(id=related_class_id)
            else:
                validated_data['related_class'] = None

        return super().update(instance, validated_data)


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer for DeviceToken model."""
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = DeviceToken
        fields = [
            'id', 'user', 'user_id', 'device_type', 'device_token',
            'device_name', 'is_active',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_user_id(self, value):
        """Validate that the user exists."""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate_device_token(self, value):
        """Validate that device token is not empty."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Device token cannot be empty.")
        return value

    def validate(self, attrs):
        """Validate device token data."""
        user_id = attrs.get('user_id')
        device_token = attrs.get('device_token')
        device_type = attrs.get('device_type')

        # Check if user exists
        if user_id:
            try:
                User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'user_id': 'User does not exist.'
                })

        # Check if device token is unique (for creation)
        if device_token and not getattr(self, 'instance', None):
            if DeviceToken.objects.filter(device_token=device_token).exists():
                raise serializers.ValidationError({
                    'device_token': 'A device with this token already exists.'
                })

        return attrs

    def create(self, validated_data):
        """Create and return a new device token."""
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update and return an existing device token."""
        user_id = validated_data.pop('user_id', None)
        if user_id is not None:
            if user_id:
                validated_data['user'] = User.objects.get(id=user_id)
            else:
                validated_data['user'] = None
        return super().update(instance, validated_data)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model."""
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'description',
            'subject_template', 'body_template',
            'template_variables', 'example_data',
            'is_active',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_template_variables(self, value):
        """Validate that template_variables is a comma-separated list if provided."""
        if value:
            # Just basic validation - ensure it's a string
            if not isinstance(value, str):
                raise serializers.ValidationError("Template variables must be a string.")
            # Could add more validation here if needed
        return value

    def validate_example_data(self, value):
        """Validate that example_data is valid JSON if provided."""
        if value:
            import json
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Example data must be valid JSON.")
        return value