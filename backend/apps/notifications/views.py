from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone
from .models import NotificationType, Notification, DeviceToken, NotificationTemplate
from .serializers import (
    NotificationTypeSerializer,
    NotificationSerializer,
    DeviceTokenSerializer,
    NotificationTemplateSerializer
)
from apps.students.models import Student
from apps.accounts.models import User


class NotificationTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification types.
    """
    queryset = NotificationType.objects.all()
    serializer_class = NotificationTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'can_send_email', 'can_send_sms', 'can_send_push', 'can_send_in_app',
        'is_active', 'is_enabled_for_students', 'is_enabled_for_staff'
    ]
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['display_name', 'created_at']
    ordering = ['display_name']

    def get_queryset(self):
        """
        Optionally restricts the returned notification types based on query parameters.
        """
        queryset = NotificationType.objects.select_related('created_by', 'updated_by')
        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'recipient', 'recipient_staff', 'notification_type',
        'channel', 'status'
    ]
    search_fields = [
        'subject', 'body',
        'recipient__first_name', 'recipient__last_name', 'recipient__student_id',
        'recipient_staff__first_name', 'recipient_staff__last_name',
        'notification_type__display_name'
    ]
    ordering_fields = ['created_at', 'sent_at', 'delivered_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned notifications based on query parameters.
        """
        queryset = Notification.objects.select_related(
            'recipient', 'recipient__user',
            'recipient_staff',
            'notification_type',
            'created_by', 'updated_by'
        ).prefetch_related(
            'related_course', 'related_class'
        )

        # Filter by recipient type if provided
        recipient_type = self.request.query_params.get('recipient_type')
        if recipient_type == 'student':
            queryset = queryset.filter(recipient__isnull=False, recipient_staff__isnull=True)
        elif recipient_type == 'staff':
            queryset = queryset.filter(recipient__isnull=True, recipient_staff__isnull=False)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        # Filter by delivery status
        delivery_status = self.request.query_params.get('delivery_status')
        if delivery_status == 'sent':
            queryset = queryset.filter(status__in=['sent', 'delivered'])
        elif delivery_status == 'failed':
            queryset = queryset.filter(status='failed')
        elif delivery_status == 'pending':
            queryset = queryset.filter(status='pending')
        elif delivery_status == 'delivered':
            queryset = queryset.filter(status='delivered')

        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Send a notification.
        In a real implementation, this would integrate with email/SMS/push services.
        """
        notification = self.get_object()

        if notification.status != 'pending':
            return Response(
                {'error': 'Only pending notifications can be sent.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # In a real implementation, this would send the notification
            # via the appropriate channel (email, SMS, push, etc.)
            # For now, we'll just mark it as sent

            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.updated_by = request.user
            notification.save()

            serializer = self.get_serializer(notification)
            return Response({
                'message': 'Notification sent successfully',
                'notification': serializer.data
            })
        except Exception as e:
            notification.status = 'failed'
            notification.failure_reason = str(e)
            notification.failed_at = timezone.now()
            notification.updated_by = request.user
            notification.save()

            return Response(
                {'error': 'Failed to send notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a notification.
        """
        notification = self.get_object()

        if notification.status not in ['pending', 'sent']:
            return Response(
                {'error': 'Only pending or sent notifications can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notification.status = 'cancelled'
        notification.updated_by = request.user
        notification.save()

        return Response({'status': 'notification cancelled'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get notification statistics.
        """
        queryset = self.get_queryset()

        # Total notifications
        total_notifications = queryset.count()

        # Notifications by status
        status_counts = queryset.values('status').annotate(count=models.Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Notifications by channel
        channel_counts = queryset.values('channel').annotate(count=models.Count('id'))
        channel_dict = {item['channel']: item['count'] for item in channel_counts}

        # Notifications by type
        type_counts = queryset.values('notification_type__display_name').annotate(count=models.Count('id'))
        type_dict = {item['notification_type__display_name']: item['count'] for item in type_counts}

        # Recent notifications (last 24 hours)
        last_24_hours = timezone.now() - timezone.timedelta(hours=24)
        recent_count = queryset.filter(created_at__gte=last_24_hours).count()

        data = {
            'total_notifications': total_notifications,
            'status_breakdown': status_dict,
            'channel_breakdown': channel_dict,
            'type_breakdown': type_dict,
            'recent_count': recent_count
        }

        return Response(data)


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing device tokens.
    """
    queryset = DeviceToken.objects.all()
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device_type', 'is_active']
    search_fields = ['device_name', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned device tokens based on query parameters.
        """
        queryset = DeviceToken.objects.select_related(
            'user', 'user__user', 'created_by', 'updated_by'
        )

        # Filter by user if provided
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a device token.
        """
        device_token = self.get_object()
        device_token.is_active = False
        device_token.updated_by = request.user
        device_token.save()

        return Response({'status': 'device token deactivated'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a device token.
        """
        device_token = self.get_object()
        device_token.is_active = True
        device_token.updated_by = request.user
        device_token.save()

        return Response({'status': 'device token activated'})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification templates.
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """
        Optionally restricts the returned notification templates based on query parameters.
        """
        queryset = NotificationTemplate.objects.select_related('created_by', 'updated_by')
        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a notification template.
        """
        template = self.get_object()
        template.is_active = not template.is_active
        template.updated_by = request.user
        template.save()

        return Response({
            'message': f'Template "{template.name}" is now {"active" if template.is_active else "inactive"}',
            'is_active': template.is_active
        })

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """
        Preview a notification template with example data.
        """
        template = self.get_object()

        # Get example data if provided
        example_data = {}
        if template.example_data:
            import json
            try:
                example_data = json.loads(template.example_data)
            except json.JSONDecodeError:
                pass  # Use empty example data

        # In a real implementation, we would render the template with the data
        # For now, we'll just return the template structure

        return Response({
            'template': NotificationTemplateSerializer(template).data,
            'example_data': example_data,
            'preview_subject': template.subject_template.format(**example_data) if template.subject_template and example_data else template.subject_template,
            'preview_body': template.body_template.format(**example_data) if template.body_template and example_data else template.body_template
        })