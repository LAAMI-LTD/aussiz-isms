from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4
from .models import IELTSResult, IELTSResultVerification, IELTSResultAudit
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest, IELTSTestAttempt


class IELTSResultTestCase(TestCase):
    """Test case for IELTS results models."""

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

        # Create a test attempt
        self.attempt = IELTSTestAttempt.objects.create(
            student=self.student,
            test=self.test,
            status='completed',
            overall_band_score=7.5,
            created_by=self.user
        )

    def test_result_creation(self):
        """Test creating an IELTS result."""
        result = IELTSResult.objects.create(
            student=self.student,
            test=self.test,
            attempt=self.attempt,
            listening_band_score=8.0,
            reading_band_score=7.5,
            writing_band_score=7.0,
            speaking_band_score=7.5,
            overall_band_score=7.5,
            result_status='released',
            result_id='IELTS2023001',
            release_date=timezone.now(),
            expiry_date=timezone.now().date() + timedelta(days=365*2),
            created_by=self.user
        )

        self.assertEqual(result.student, self.student)
        self.assertEqual(result.test, self.test)
        self.assertEqual(result.attempt, self.attempt)
        self.assertEqual(result.listening_band_score, 8.0)
        self.assertEqual(result.reading_band_score, 7.5)
        self.assertEqual(result.writing_band_score, 7.0)
        self.assertEqual(result.speaking_band_score, 7.5)
        self.assertEqual(result.overall_band_score, 7.5)
        self.assertEqual(result.result_status, 'released')
        self.assertEqual(result.result_id, 'IELTS2023001')
        self.assertTrue(result.is_verified == False)  # Default value
        self.assertEqual(str(result), f'{self.student.get_full_name()} - {self.test.title} ({result.overall_band_score})')

    def test_result_overall_band_calculation(self):
        """Test that overall band score is correctly calculated from section scores."""
        result = IELTSResult.objects.create(
            student=self.student,
            test=self.test,
            attempt=self.attempt,
            listening_band_score=8.0,
            reading_band_score=7.5,
            writing_band_score=7.0,
            speaking_band_score=7.5,
            # overall_band_score not provided - should be auto-calculated
            result_status='released',
            result_id='IELTS2023002',
            release_date=timezone.now(),
            expiry_date=timezone.now().date() + timedelta(days=365*2),
            created_by=self.user
        )

        # Expected overall band score: (8.0 + 7.5 + 7.0 + 7.5) / 4 = 7.5
        # Rounded to nearest 0.5: 7.5
        self.assertEqual(result.overall_band_score, 7.5)

    def test_result_verification_creation(self):
        """Test creating a result verification."""
        # First create a result
        result = IELTSResult.objects.create(
            student=self.student,
            test=self.test,
            attempt=self.attempt,
            listening_band_score=8.0,
            reading_band_score=7.5,
            writing_band_score=7.0,
            speaking_band_score=7.5,
            overall_band_score=7.5,
            result_status='released',
            result_id='IELTS2023003',
            release_date=timezone.now(),
            expiry_date=timezone.now().date() + timedelta(days=365*2),
            created_by=self.user
        )

        # Create a verification
        verification = IELTSResultVerification.objects.create(
            result=result,
            requestor_name='Test University',
            requestor_institution='Test University',
            requestor_email='verifications@testuni.edu',
            verification_type='institution',
            shared_overall_score=True,
            shared_section_scores=True,
            shared_personal_details=False,
            created_by=self.user
        )

        self.assertEqual(verification.result, result)
        self.assertEqual(verification.requestor_name, 'Test University')
        self.assertEqual(verification.status, 'pending')  # Default value
        self.assertEqual(verification.verification_type, 'institution')
        self.assertTrue(verification.shared_overall_score)
        self.assertTrue(verification.shared_section_scores)
        self.assertFalse(verification.shared_personal_details)

        # Check that the result's verification count was updated
        result.refresh_from_db()
        self.assertEqual(result.verification_count, 1)
        self.assertTrue(result.is_verified)
        self.assertIsNotNone(result.last_verified_at)
        self.assertEqual(result.last_verified_by, self.user)

    def test_result_audit_creation(self):
        """Test creating an audit entry for a result."""
        # First create a result
        result = IELTSResult.objects.create(
            student=self.student,
            test=self.test,
            attempt=self.attempt,
            listening_band_score=8.0,
            reading_band_score=7.5,
            writing_band_score=7.0,
            speaking_band_score=7.5,
            overall_band_score=7.5,
            result_status='released',
            result_id='IELTS2023004',
            release_date=timezone.now(),
            expiry_date=timezone.now().date() + timedelta(days=365*2),
            created_by=self.user
        )

        # Create an audit entry
        audit = IELTSResultAudit.objects.create(
            result=result,
            field_name='remarks',
            old_value='',
            new_value='Verified result for university application',
            changed_by=self.user,
            change_reason='Added remarks for verification'
        )

        self.assertEqual(audit.result, result)
        self.assertEqual(audit.field_name, 'remarks')
        self.assertEqual(audit.old_value, '')
        self.assertEqual(audit.new_value, 'Verified result for university application')
        self.assertEqual(audit.changed_by, self.user)
        self.assertEqual(audit.change_reason, 'Added remarks for verification')

    def test_result_expiry_check(self):
        """Test checking if a result has expired."""
        # Create a result that expires in the past
        expired_result = IELTSResult.objects.create(
            student=self.student,
            test=self.test,
            attempt=self.attempt,
            listening_band_score=6.5,
            reading_band_score=6.0,
            writing_band_score=5.5,
            speaking_band_score=6.0,
            overall_band_score=6.0,
            result_status='released',
            result_id='IELTS2020001',
            release_date=timezone.now() - timedelta(days=365*3),  # Released 3 years ago
            expiry_date=timezone.now().date() - timedelta(days=365),  # Expired 1 year ago
            created_by=self.user
        )

        # Create a result that expires in the future
        future_result = IELTSResult.objects.create(
            student=self.student,
            test=self.test,
            attempt=self.attempt,
            listening_band_score=7.5,
            reading_band_score=7.0,
            writing_band_score=6.5,
            speaking_band_score=7.0,
            overall_band_score=7.0,
            result_status='released',
            result_id='IELTS2025001',
            release_date=timezone.now(),
            expiry_date=timezone.now().date() + timedelta(days=365*2),  # Expires in 2 years
            created_by=self.user
        )

        self.assertTrue(expired_result.is_expired)
        self.assertFalse(future_result.is_expired)