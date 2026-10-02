from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.students.models import Student
from apps.courses.models import Course, CourseCategory
import datetime

User = get_user_model()


class NotificationTypeViewSetTestCase(TestCase):
    """Test case for NotificationTypeViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create tutor role and assign to user
        tutor_role, created = Role.objects.get_or_create(
            name='Tutor',
            defaults={'description': 'Tutor role'}
        )
        self.user.roles.add(tutor_role)
        self.client.force_authenticate(user=self.user)

        self.notification_type = NotificationType.objects.create(
            name='test_notification',
            display_name='Test Notification',
            description='Test notification description',
            can_send_email=True,
            can_send_sms=False,
            can_send_push=True,
            can_send_in_app=True,
            is_active=True,
            created_by=self.user
        )

    def test_list_notification_types(self):
        """Test retrieving a list of notification types."""
        url = reverse('notifications:notificationtype-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_notification_type(self):
        """Test retrieving a specific notification type."""
        url = reverse('notifications:notificationtype-detail', kwargs={'pk': self.notification_type.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.notification_type.name)

    def test_create_notification_type(self):
        """Test creating a new notification type."""
        url = reverse('notifications:notificationtype-list')
        data = {
            'name': 'email_notification',
            'display_name': 'Email Notification',
            'description': 'Email notification description',
            'can_send_email': True,
            'can_send_sms': False,
            'can_send_push': False,
            'can_send_in_app': True,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NotificationType.objects.count(), 2)

    def test_update_notification_type(self):
        """Test updating a notification type."""
        url = reverse('notifications:notificationtype-detail', kwargs={'pk': self.notification_type.pk})
        data = {
            'name': self.notification_type.name,
            'display_name': 'Updated Test Notification',
            'description': self.notification_type.description,
            'can_send_email': self.notification_type.can_send_email,
            'can_send_sms': self.notification_type.can_send_sms,
            'can_send_push': self.notification_type.can_send_push,
            'can_send_in_app': self.notification_type.can_send_in_app,
            'is_active': self.notification_type.is_active
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification_type.refresh_from_db()
        self.assertEqual(self.notification_type.display_name, 'Updated Test Notification')


class NotificationViewSetTestCase(TestCase):
    """Test case for NotificationViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create tutor role and assign to user
        tutor_role, created = Role.objects.get_or_create(
            name='Tutor',
            defaults={'description': 'Tutor role'}
        )
        self.user.roles.add(tutor_role)
        self.client.force_authenticate(user=self.user)

        self.student = Student.objects.create(
            student_id='STU001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone_number='1234567890',
            date_of_birth=datetime.date(2000, 1, 1),
            gender='male',
            address='123 Test Street',
            city='Test City',
            country='Test Country',
            course_enrolled='IELTS Preparation',
            enrollment_date=datetime.date.today()
        )

        self.notification_type = NotificationType.objects.create(
            name='test_notification',
            display_name='Test Notification',
            description='Test notification description',
            can_send_email=True,
            can_send_sms=False,
            can_send_push=True,
            can_send_in_app=True,
            email_subject_template='Test Subject: {student_name}',
            email_body_template='Hello {student_name}, this is a test notification.',
            is_active=True,
            created_by=self.user
        )

    def test_list_notifications(self):
        """Test retrieving a list of notifications."""
        url = reverse('notifications:notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_notification(self):
        """Test creating a new notification."""
        url = reverse('notifications:notification-list')
        data = {
            'recipient_id': str(self.student.id),
            'notification_type_id': str(self.notification_type.id),
            'channel': 'email',
            'subject': 'Test Subject',
            'body': 'Test Body'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)

    def test_update_notification(self):
        """Test updating a notification."""
        notification = Notification.objects.create(
            recipient=self.student,
            notification_type=self.notification_type,
            channel='email',
            subject='Original Subject',
            body='Original Body',
            status='pending',
            created_by=self.user
        )

        url = reverse('notifications:notification-detail', kwargs={'pk': notification.pk})
        data = {
            'recipient_id': str(self.student.id),
            'notification_type_id': str(self.notification_type.id),
            'channel': 'email',
            'subject': 'Updated Subject',
            'body': 'Updated Body',
            'status': 'sent'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertEqual(notification.subject, 'Updated Subject')

    def test_send_notification(self):
        """Test sending a notification."""
        notification = Notification.objects.create(
            recipient=self.student,
            notification_type=self.notification_type,
            channel='email',
            subject='Test Subject',
            body='Test Body',
            status='pending',
            created_by=self.user
        )

        url = reverse('notifications:notification-send', kwargs={'pk': notification.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Check that notification was marked as sent
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'sent')
        self.assertIsNotNone(notification.sent_at)


class DeviceTokenViewSetTestCase(TestCase):
    """Test case for DeviceTokenViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create tutor role and assign to user
        tutor_role, created = Role.objects.get_or_create(
            name='Tutor',
            defaults={'description': 'Tutor role'}
        )
        self.user.roles.add(tutor_role)
        self.client.force_authenticate(user=self.user)

        self.device_token = DeviceToken.objects.create(
            user=self.user,
            device_type='ios',
            device_token='abc123def456',
            device_name='iPhone 12',
            is_active=True,
            created_by=self.user
        )

    def test_list_device_tokens(self):
        """Test retrieving a list of device tokens."""
        url = reverse('notifications:devicetoken-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_device_token(self):
        """Test retrieving a specific device token."""
        url = reverse('notifications:devicetoken-detail', kwargs={'pk': self.device_token.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['device_type'], self.device_token.device_type)

    def test_create_device_token(self):
        """Test creating a new device token."""
        url = reverse('notifications:devicetoken-list')
        data = {
            'user_id': str(self.user.id),
            'device_type': 'android',
            'device_token': 'xyz789uvw012',
            'device_name': 'Samsung Galaxy S21',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DeviceToken.objects.count(), 2)

    def test_deactivate_device_token(self):
        """Test deactivating a device token."""
        url = reverse('notifications:devicetoken-deactivate', kwargs={'pk': self.device_token.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'device token deactivated')

        # Check that device token was deactivated
        self.device_token.refresh_from_db()
        self.assertFalse(self.device_token.is_active)


class NotificationTemplateViewSetTestCase(TestCase):
    """Test case for NotificationTemplateViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create tutor role and assign to user
        tutor_role, created = Role.objects.get_or_create(
            name='Tutor',
            defaults={'description': 'Tutor role'}
        )
        self.user.roles.add(tutor_role)
        self.client.force_authenticate(user=self.user)

        self.notification_template = NotificationTemplate.objects.create(
            name='welcome_email',
            template_type='email',
            description='Welcome email template',
            subject_template='Welcome to AUSSIZ-ISMS, {student_name}!',
            body_template='Hello {student_name},\n\nWelcome to our institution. Your student ID is {student_id}.',
            template_variables='student_name,student_id',
            example_data='{"student_name": "John Doe", "student_id": "STU001"}',
            is_active=True,
            created_by=self.user
        )

    def test_list_notification_templates(self):
        """Test retrieving a list of notification templates."""
        url = reverse('notifications:notificationtemplate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_notification_template(self):
        """Test retrieving a specific notification template."""
        url = reverse('notifications:notificationtemplate-detail', kwargs={'pk': self.notification_template.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.notification_template.name)

    def test_toggle_active(self):
        """Test toggling the active status of a notification template."""
        url = reverse('notifications:notificationtemplate-toggle-active', kwargs={'pk': self.notification_template.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_active', response.data)
        # Should have toggled from True to False
        self.assertFalse(response.data['is_active'])

        # Toggle again
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have toggled from False to True
        self.assertTrue(response.data['is_active'])

    def test_preview(self):
        """Test previewing a notification template."""
        url = reverse('notifications:notificationtemplate-preview', kwargs={'pk': self.notification_template.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('preview_subject', response.data)
        self.assertIn('preview_body', response.data)