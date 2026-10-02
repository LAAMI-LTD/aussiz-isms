from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.finance.models import Payment, Invoice
from apps.students.models import Student
from apps.accounts.models import User, Role
import datetime

User = get_user_model()


class ReportCategoryViewSetTestCase(TestCase):
    """Test case for ReportCategoryViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create finance role and assign to user
        finance_role, created = Role.objects.get_or_create(
            name='Finance',
            defaults={'description': 'Finance role'}
        )
        self.user.roles.add(finance_role)
        self.client.force_authenticate(user=self.user)

    def test_list_report_categories(self):
        """Test retrieving a list of report categories."""
        url = reverse('reports:categories-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_report_category(self):
        """Test creating a new report category."""
        url = reverse('reports:categories-list')
        data = {
            'name': 'Financial Reports',
            'description': 'Reports related to financial data',
            'icon': 'fa-dollar-sign',
            'color': '#10B981',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReportCategory.objects.count(), 1)


class ReportTemplateViewSetTestCase(TestCase):
    """Test case for ReportTemplateViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create finance role and assign to user
        finance_role, created = Role.objects.get_or_create(
            name='Finance',
            defaults={'description': 'Finance role'}
        )
        self.user.roles.add(finance_role)
        self.client.force_authenticate(user=self.user)

        # Create a category
        self.category = ReportCategory.objects.create(
            name='Financial Reports',
            description='Reports related to financial data',
            is_active=True,
            created_by=self.user
        )

    def test_list_report_templates(self):
        """Test retrieving a list of report templates."""
        url = reverse('reports:templates-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_report_template(self):
        """Test creating a new report template."""
        url = reverse('reports:templates-list')
        data = {
            'name': 'Monthly Revenue Report',
            'report_type': 'revenue_report',
            'category': str(self.category.id),
            'description': 'Monthly revenue summary report',
            'format': 'pdf',
            'is_active': True,
            'is_scheduled': True,
            'parameters_schema': {
                "type": "object",
                "properties": {
                    "month": {"type": "integer", "minimum": 1, "maximum": 12},
                    "year": {"type": "integer"}
                }
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReportTemplate.objects.count(), 1)


class GeneratedReportViewSetTestCase(TestCase):
    """Test case for GeneratedReportViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create finance role and assign to user
        finance_role, created = Role.objects.get_or_create(
            name='Finance',
            defaults={'description': 'Finance role'}
        )
        self.user.roles.add(finance_role)
        self.client.force_authenticate(user=self.user)

        # Create a category
        self.category = ReportCategory.objects.create(
            name='Financial Reports',
            description='Reports related to financial data',
            is_active=True,
            created_by=self.user
        )

        # Create a template
        self.template = ReportTemplate.objects.create(
            name='Monthly Revenue Report',
            report_type='revenue_report',
            category=self.category,
            description='Monthly revenue summary report',
            format='pdf',
            is_active=True,
            is_scheduled=True,
            created_by=self.user
        )

    def test_list_generated_reports(self):
        """Test retrieving a list of generated reports."""
        url = reverse('reports:generated-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_generated_report(self):
        """Test creating a new generated report."""
        url = reverse('reports:generated-list')
        data = {
            'template': str(self.template.id),
            'name': 'January 2026 Revenue Report',
            'description': 'Revenue report for January 2026',
            'format': 'pdf',
            'parameters': {
                'month': 1,
                'year': 2026
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GeneratedReport.objects.count(), 1)


class ReportScheduleViewSetTestCase(TestCase):
    """Test case for ReportScheduleViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create finance role and assign to user
        finance_role, created = Role.objects.get_or_create(
            name='Finance',
            defaults={'description': 'Finance role'}
        )
        self.user.roles.add(finance_role)
        self.client.force_authenticate(user=self.user)

        # Create a category
        self.category = ReportCategory.objects.create(
            name='Financial Reports',
            description='Reports related to financial data',
            is_active=True,
            created_by=self.user
        )

        # Create a template
        self.template = ReportTemplate.objects.create(
            name='Monthly Revenue Report',
            report_type='revenue_report',
            category=self.category,
            description='Monthly revenue summary report',
            format='pdf',
            is_active=True,
            is_scheduled=True,
            created_by=self.user
        )

    def test_list_report_schedules(self):
        """Test retrieving a list of report schedules."""
        url = reverse('reports:schedules-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_report_schedule(self):
        """Test creating a new report schedule."""
        url = reverse('reports:schedules-list')
        data = {
            'template': str(self.template.id),
            'name': 'Monthly Revenue Schedule',
            'description': 'Schedule for monthly revenue report',
            'frequency': 'monthly',
            'day_of_month': 1,
            'time_of_day': '09:00:00',
            'parameters': {
                'month': 1,
                'year': 2026
            },
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReportSchedule.objects.count(), 1)