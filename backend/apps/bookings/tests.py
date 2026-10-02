from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4
from .models import IELTSExamCenter, IELTSExamDate, IELTSExamBooking
from apps.students.models import Student
from apps.accounts.models import User


class IELTSExamBookingTestCase(TestCase):
    """Test case for IELTS exam booking models."""

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

        # Create a test exam center
        self.center = IELTSExamCenter.objects.create(
            name='Test Exam Center',
            address='123 Exam Street',
            city='Exam City',
            country='Exam Country',
            phone_number='1234567890',
            email='exam@example.com',
            daily_capacity=50,
            created_by=self.user
        )

        # Create a test exam date
        self.exam_date = IELTSExamDate.objects.create(
            center=self.center,
            exam_type='academic',
            exam_date=timezone.now().date() + timedelta(days=30),
            registration_deadline=timezone.now().date() + timedelta(days=20),
            total_slots=20,
            exam_fee=250.00,
            created_by=self.user
        )

    def test_exam_center_creation(self):
        """Test creating an exam center."""
        self.assertEqual(self.center.name, 'Test Exam Center')
        self.assertEqual(self.center.city, 'Exam City')
        self.assertTrue(self.center.is_active)
        self.assertEqual(str(self.center), 'Test Exam Center, Exam City, Exam Country')

    def test_exam_date_creation(self):
        """Test creating an exam date."""
        self.assertEqual(self.exam_date.center, self.center)
        self.assertEqual(self.exam_date.exam_type, 'academic')
        self.assertEqual(self.exam_date.total_slots, 20)
        self.assertEqual(self.exam_date.filled_slots, 0)
        self.assertEqual(self.exam_date.available_slots, 20)
        self.assertTrue(self.exam_date.is_active)

    def test_exam_date_available_slots_calculation(self):
        """Test that available slots are calculated correctly."""
        # Initially available slots should equal total slots
        self.assertEqual(self.exam_date.available_slots, 20)

        # Create a booking to fill a slot
        IELTSExamBooking.objects.create(
            student=self.student,
            exam_date=self.exam_date,
            status='confirmed',
            amount_paid=250.00,
            created_by=self.user
        )

        # Refresh from database
        self.exam_date.refresh_from_db()

        # Available slots should now be 19
        self.assertEqual(self.exam_date.filled_slots, 1)
        self.assertEqual(self.exam_date.available_slots, 19)

    def test_exam_booking_creation(self):
        """Test creating an exam booking."""
        booking = IELTSExamBooking.objects.create(
            student=self.student,
            exam_date=self.exam_date,
            status='pending',
            amount_paid=0.00,
            created_by=self.user
        )

        self.assertEqual(booking.student, self.student)
        self.assertEqual(booking.exam_date, self.exam_date)
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.amount_paid, 0.00)
        self.assertEqual(str(booking), f'{self.student.get_full_name()} - {self.exam_date} (pending)')

    def test_exam_booking_confirmation(self):
        """Test confirming a pending booking."""
        booking = IELTSExamBooking.objects.create(
            student=self.student,
            exam_date=self.exam_date,
            status='pending',
            amount_paid=250.00,
            created_by=self.user
        )

        # Confirm the booking
        booking.status = 'confirmed'
        booking.save()

        # Refresh from database
        booking.refresh_from_db()
        self.exam_date.refresh_from_db()

        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(self.exam_date.filled_slots, 1)
        self.assertEqual(self.exam_date.available_slots, 19)

    def test_exam_booking_cancellation(self):
        """Test cancelling a confirmed booking."""
        # Create a confirmed booking
        booking = IELTSExamBooking.objects.create(
            student=self.student,
            exam_date=self.exam_date,
            status='confirmed',
            amount_paid=250.00,
            created_by=self.user
        )

        # Confirm it first (to update filled slots)
        booking.status = 'confirmed'
        booking.save()

        # Refresh from database
        self.exam_date.refresh_from_db()
        initial_filled_slots = self.exam_date.filled_slots

        # Now cancel the booking
        booking.status = 'cancelled'
        booking.save()

        # Refresh from database
        booking.refresh_from_db()
        self.exam_date.refresh_from_db()

        self.assertEqual(booking.status, 'cancelled')
        # Filled slots should decrease by 1
        self.assertEqual(self.exam_date.filled_slots, initial_filled_slots - 1)

    def test_duplicate_booking_prevention(self):
        """Test that duplicate bookings for the same exam date are prevented."""
        # Create first booking
        IELTSExamBooking.objects.create(
            student=self.student,
            exam_date=self.exam_date,
            status='pending',
            amount_paid=0.00,
            created_by=self.user
        )

        # Try to create second booking for same student and exam date
        with self.assertRaises(Exception):  # Should raise validation error
            IELTSExamBooking.objects.create(
                student=self.student,
                exam_date=self.exam_date,
                status='pending',
                amount_paid=0.00,
                created_by=self.user
            )