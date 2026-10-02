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


class ReceiptViewSetTestCase(TestCase):
    """Test case for ReceiptViewSet."""

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

        # Create a student
        self.student = Student.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='ABC123456',
            phone_number='+254700000000',
            email='john.doe@example.com',
            address='123 Test Street'
        )

        # Create an invoice
        self.invoice = Invoice.objects.create(
            student=self.student,
            issue_date=datetime.date.today(),
            due_date=datetime.date.today() + datetime.timedelta(days=30),
            subtotal=1000.00,
            tax_amount=160.00,
            total_amount=1160.00,
            created_by=self.user
        )

        # Create a payment
        self.payment = Payment.objects.create(
            student=self.student,
            invoice=self.invoice,
            amount=1160.00,
            payment_method='bank_transfer',
            status='processed',
            created_by=self.user
        )

    def test_list_receipts(self):
        """Test retrieving a list of receipts."""
        url = reverse('receipts:receipts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_retrieve_receipt(self):
        """Test retrieving a specific receipt."""
        # First create a receipt
        receipt = Receipt.objects.create(
            payment=self.payment,
            invoice=self.invoice,
            created_by=self.user
        )
        url = reverse('receipts:receipts-detail', kwargs={'pk': receipt.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['receipt_number'], receipt.receipt_number)

    def test_create_receipt(self):
        """Test creating a new receipt."""
        url = reverse('receipts:receipts-list')
        data = {
            'payment': str(self.payment.id),
            'notes': 'Test receipt',
            'terms_and_conditions': 'Standard terms apply'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Receipt.objects.count(), 1)

    def test_generate_receipt_from_payment(self):
        """Test generating a receipt from a payment."""
        url = reverse('receipts:receipts-generate-from-payment')
        data = {
            'payment_id': str(self.payment.id),
            'notes': 'Test generated receipt',
            'terms_and_conditions': 'Standard terms apply'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Receipt.objects.count(), 1)
        self.assertIn('message', response.data)
        self.assertIn('receipt', response.data)

    def test_generate_pdf(self):
        """Test generating PDF for a receipt."""
        # First create a receipt
        receipt = Receipt.objects.create(
            payment=self.payment,
            invoice=self.invoice,
            created_by=self.user
        )
        url = reverse('receipts:receipts-generate-pdf', kwargs={'pk': receipt.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('pdf_generated_at', response.data)

    def test_cancel_receipt(self):
        """Test cancelling a receipt."""
        # First create a receipt
        receipt = Receipt.objects.create(
            payment=self.payment,
            invoice=self.invoice,
            created_by=self.user
        )
        url = reverse('receipts:receipts-cancel', kwargs={'pk': receipt.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Receipt cancelled successfully')
        self.assertTrue(response.data['is_cancelled'])

        # Check that the receipt was actually updated
        receipt.refresh_from_db()
        self.assertTrue(receipt.is_cancelled)
        self.assertIsNotNone(receipt.cancelled_at)

    def test_receipt_history(self):
        """Test retrieving history for a receipt."""
        # First create a receipt
        receipt = Receipt.objects.create(
            payment=self.payment,
            invoice=self.invoice,
            created_by=self.user
        )
        # Update the receipt to create history
        receipt.notes = 'Updated notes'
        receipt.save()

        url = reverse('receipts:receipts-history', kwargs={'pk': receipt.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)  # At least creation and update


class ReceiptItemViewSetTestCase(TestCase):
    """Test case for ReceiptItemViewSet."""

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

        # Create a student
        self.student = Student.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='ABC123456',
            phone_number='+254700000000',
            email='john.doe@example.com',
            address='123 Test Street'
        )

        # Create an invoice
        self.invoice = Invoice.objects.create(
            student=self.student,
            issue_date=datetime.date.today(),
            due_date=datetime.date.today() + datetime.timedelta(days=30),
            subtotal=1000.00,
            tax_amount=160.00,
            total_amount=1160.00,
            created_by=self.user
        )

        # Create a payment
        self.payment = Payment.objects.create(
            student=self.student,
            invoice=self.invoice,
            amount=1160.00,
            payment_method='bank_transfer',
            status='processed',
            created_by=self.user
        )

        # Create a receipt
        self.receipt = Receipt.objects.create(
            payment=self.payment,
            invoice=self.invoice,
            created_by=self.user
        )

    def test_list_receipt_items(self):
        """Test retrieving a list of receipt items."""
        url = reverse('receipts:items-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_receipt_item(self):
        """Test creating a new receipt item."""
        url = reverse('receipts:items-list')
        data = {
            'receipt': str(self.receipt.id),
            'description': 'Test item',
            'quantity': 2,
            'unit_price': 100.00,
            'is_taxable': True,
            'tax_rate': 0.16
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReceiptItem.objects.count(), 1)


class ReceiptHistoryViewSetTestCase(TestCase):
    """Test case for ReceiptHistoryViewSet."""

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

        # Create a student
        self.student = Student.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='ABC123456',
            phone_number='+254700000000',
            email='john.doe@example.com',
            address='123 Test Street'
        )

        # Create an invoice
        self.invoice = Invoice.objects.create(
            student=self.student,
            issue_date=datetime.date.today(),
            due_date=datetime.date.today() + datetime.timedelta(days=30),
            subtotal=1000.00,
            tax_amount=160.00,
            total_amount=1160.00,
            created_by=self.user
        )

        # Create a payment
        self.payment = Payment.objects.create(
            student=self.student,
            invoice=self.invoice,
            amount=1160.00,
            payment_method='bank_transfer',
            status='processed',
            created_by=self.user
        )

        # Create a receipt
        self.receipt = Receipt.objects.create(
            payment=self.payment,
            invoice=self.invoice,
            created_by=self.user
        )

    def test_list_receipt_history(self):
        """Test retrieving a list of receipt history entries."""
        url = reverse('receipts:history-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Creation history

    def test_create_receipt_history(self):
        """Test that history is automatically created."""
        # The receipt creation should have created a history entry
        history_count = ReceiptHistory.objects.filter(receipt=self.receipt).count()
        self.assertEqual(history_count, 1)

        # Update the receipt to create another history entry
        self.receipt.notes = 'Updated notes'
        self.receipt.save()

        history_count = ReceiptHistory.objects.filter(receipt=self.receipt).count()
        self.assertEqual(history_count, 2)  # Creation and update