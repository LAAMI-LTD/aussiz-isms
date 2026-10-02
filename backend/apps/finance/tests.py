from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4
from .models import FeeType, FeeItem, Invoice, InvoiceItem, Payment, Receipt
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest


class FinanceTestCase(TestCase):
    """Test case for finance models."""

    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create a test student
        self.student = Student.objects.create(
            student_id='STU001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone_number='1234567890',
            date_of_birth=timezone.now().date() - timedelta(days=365*20),
            gender='male',
            address='123 Test Street',
            city='Test City',
            country='Test Country',
            course_enrolled='IELTS Preparation',
            enrollment_date=timezone.now().date()
        )

        # Create a test IELTS test
        self.test = IELTSTest.objects.create(
            title='IELTS Practice Test 1',
            test_type='practice',
            test_mode='academic',
            is_active=True,
            created_by=self.user
        )

    def test_fee_type_creation(self):
        """Test creating a fee type."""
        fee_type = FeeType.objects.create(
            name='Tuition Fee',
            category='tuition',
            description='Monthly tuition fee',
            default_amount=500.00,
            is_taxable=False,
            created_by=self.user
        )

        self.assertEqual(fee_type.name, 'Tuition Fee')
        self.assertEqual(fee_type.category, 'tuition')
        self.assertEqual(fee_type.default_amount, 500.00)
        self.assertFalse(fee_type.is_taxable)
        self.assertTrue(fee_type.is_active)
        self.assertEqual(str(fee_type), 'Tuition - Tuition Fee')

    def test_fee_item_creation(self):
        """Test creating a fee item."""
        # Create fee type first
        fee_type = FeeType.objects.create(
            name='Registration Fee',
            category='registration',
            default_amount=100.00,
            created_by=self.user
        )

        # Create fee item
        fee_item = FeeItem.objects.create(
            fee_type=fee_type,
            student=self.student,
            description='Semester registration fee',
            amount=100.00,
            due_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )

        self.assertEqual(fee_item.fee_type, fee_type)
        self.assertEqual(fee_item.student, self.student)
        self.assertEqual(fee_item.description, 'Semester registration fee')
        self.assertEqual(fee_item.amount, 100.00)
        self.assertFalse(fee_item.is_paid)
        self.assertTrue(fee_item.is_active)

        # Test discounted amount calculation
        fee_item.discount_percentage = 10.0  # 10% discount
        fee_item.save()
        self.assertEqual(fee_item.discounted_amount, 90.00)

    def test_invoice_creation(self):
        """Test creating an invoice."""
        # Create a fee item first
        fee_type = FeeType.objects.create(
            name='Exam Fee',
            category='exam',
            default_amount=250.00,
            created_by=self.user
        )

        fee_item = FeeItem.objects.create(
            fee_type=fee_type,
            student=self.student,
            description='IELTS exam fee',
            amount=250.00,
            due_date=timezone.now().date() + timedelta(days=15),
            created_by=self.user
        )

        # Create invoice
        invoice = Invoice.objects.create(
            student=self.student,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            subtotal=250.00,
            tax_amount=0.00,  # No tax for this example
            created_by=self.user
        )

        # Create invoice item
        invoice_item = InvoiceItem.objects.create(
            invoice=invoice,
            fee_item=fee_item,
            description='IELTS exam fee',
            quantity=1,
            unit_price=250.00,
            is_taxable=False,
            created_by=self.user
        )

        self.assertEqual(invoice.student, self.student)
        self.assertEqual(invoice.issue_date, timezone.now().date())
        self.assertEqual(invoice.subtotal, 250.00)
        self.assertEqual(invoice.tax_amount, 0.00)
        self.assertEqual(invoice.total_amount, 250.00)
        self.assertEqual(invoice.status, 'draft')
        self.assertEqual(invoice.amount_paid, 0.00)

        self.assertEqual(invoice_item.invoice, invoice)
        self.assertEqual(invoice_item.fee_item, fee_item)
        self.assertEqual(invoice_item.description, 'IELTS exam fee')
        self.assertEqual(invoice_item.quantity, 1)
        self.assertEqual(invoice_item.unit_price, 250.00)
        self.assertEqual(invoice_item.line_total, 250.00)
        self.assertEqual(invoice_item.tax_amount, 0.00)

    def test_invoice_total_calculation(self):
        """Test that invoice total is calculated correctly."""
        invoice = Invoice.objects.create(
            student=self.student,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=10.00,  # 10% tax
            created_by=self.user
        )

        # Total should be subtotal + tax
        self.assertEqual(invoice.total_amount, 110.00)

    def test_payment_creation(self):
        """Test creating a payment."""
        # Create invoice first
        invoice = Invoice.objects.create(
            student=self.student,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=0.00,
            total_amount=100.00,
            created_by=self.user
        )

        # Create payment
        payment = Payment.objects.create(
            student=self.student,
            invoice=invoice,
            amount=100.00,
            payment_method='credit_card',
            status='pending',
            created_by=self.user
        )

        self.assertEqual(payment.student, self.student)
        self.assertEqual(payment.invoice, invoice)
        self.assertEqual(payment.amount, 100.00)
        self.assertEqual(payment.payment_method, 'credit_card')
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(str(payment), f'Payment {payment.payment_number} - $100.00 (Credit Card)')

        # Test processing payment
        payment.process()
        self.assertEqual(payment.status, 'processed')
        self.assertIsNotNone(payment.payment_date)

        # Check that invoice was updated
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, 100.00)
        self.assertEqual(invoice.status, 'paid')

    def test_receipt_creation(self):
        """Test creating a receipt."""
        # Create payment first
        invoice = Invoice.objects.create(
            student=self.student,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            subtotal=50.00,
            tax_amount=0.00,
            total_amount=50.00,
            created_by=self.user
        )

        payment = Payment.objects.create(
            student=self.student,
            invoice=invoice,
            amount=50.00,
            payment_method='bank_transfer',
            status='processed',
            created_by=self.user
        )

        # Create receipt
        receipt = Receipt.objects.create(
            payment=payment,
            amount=50.00,
            created_by=self.user
        )

        self.assertEqual(receipt.payment, payment)
        self.assertEqual(receipt.amount, 50.00)
        self.assertEqual(receipt.issue_date, timezone.now())
        self.assertEqual(str(receipt), f'Receipt {receipt.receipt_number} - Payment {payment.payment_number}')

        # Test that receipt number was auto-generated
        self.assertTrue(receipt.receipt_number.startswith('REC-'))
        self.assertEqual(len(receipt.receipt_number), 15)  # REC-YYYYMMDD-XXXX format

    def test_fee_item_overdue_check(self):
        """Test checking if a fee item is overdue."""
        # Create fee type
        fee_type = FeeType.objects.create(
            name='Late Fee',
            category='late',
            default_amount=50.00,
            created_by=self.user
        )

        # Create an overdue fee item
        overdue_fee = FeeItem.objects.create(
            fee_type=fee_type,
            student=self.student,
            description='Late payment fee',
            amount=50.00,
            due_date=timezone.now().date() - timedelta(days=10),  # Due 10 days ago
            created_by=self.user
        )

        # Create a future fee item
        future_fee = FeeItem.objects.create(
            fee_type=fee_type,
            student=self.student,
            description='Upcoming fee',
            amount=50.00,
            due_date=timezone.now().date() + timedelta(days=10),  # Due in 10 days
            created_by=self.user
        )

        self.assertTrue(overdue_fee.is_overdue)
        self.assertFalse(future_fee.is_overdue)