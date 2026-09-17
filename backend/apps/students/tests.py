from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Student, NextOfKin, StudentDocument
from apps.accounts.models import User
import datetime


class StudentModelTestCase(TestCase):
    """Test case for Student model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            first_name='Staff',
            last_name='User'
        )

        self.next_of_kin = NextOfKin.objects.create(
            first_name='John',
            last_name='Doe',
            relationship='Father',
            phone_number='+254700000000'
        )

    def test_student_creation(self):
        """Test that a student can be created with valid data."""
        student = Student.objects.create(
            first_name='Jane',
            last_name='Smith',
            gender='F',
            date_of_birth=datetime.date(2000, 1, 15),
            nationality='KE',
            national_id_passport='AB123456C',
            phone_number='+254712345678',
            email='jane.smith@example.com',
            address='123 Student Street, Nairobi',
            next_of_kin=self.next_of_kin,
            created_by=self.user
        )

        self.assertEqual(student.first_name, 'Jane')
        self.assertEqual(student.last_name, 'Smith')
        self.assertEqual(student.get_full_name(), 'Jane Smith')
        self.assertEqual(student.nationality, 'KE')
        self.assertEqual(student.status, 'active')  # Default status
        self.assertIsNotNone(student.student_id)  # Should be auto-generated
        self.assertTrue(student.student_id.startswith('SAKE/'))

    def test_student_id_generation(self):
        """Test that student IDs are generated correctly."""
        # Create first student
        student1 = Student.objects.create(
            first_name='Alice',
            last_name='Johnson',
            gender='F',
            date_of_birth=datetime.date(2000, 5, 20),
            nationality='KE',
            national_id_passport='CD789012E',
            phone_number='+254723456789',
            email='alice@example.com',
            address='456 Learner Ave, Nairobi',
            created_by=self.user
        )

        # Create second student
        student2 = Student.objects.create(
            first_name='Bob',
            last_name='Wilson',
            gender='M',
            date_of_birth=datetime.date(1999, 8, 10),
            nationality='KE',
            national_id_passport='EF345678G',
            phone_number='+254734567890',
            email='bob@example.com',
            address='789 Study Lane, Nairobi',
            created_by=self.user
        )

        # Both should have SAKE prefix with same month/year
        self.assertTrue(student1.student_id.startswith('SAKE/'))
        self.assertTrue(student2.student_id.startswith('SAKE/'))

        # Extract month/year part (should be same for both created in same month)
        id1_parts = student1.student_id.split('/')
        id2_parts = student2.student_id.split('/')

        # Should have same month and year (index 1 and 2)
        self.assertEqual(id1_parts[1], id2_parts[1])  # Month
        self.assertEqual(id1_parts[2], id2_parts[2])  # Year

        # Sequence numbers should be different and sequential
        seq1 = int(id1_parts[3])
        seq2 = int(id2_parts[3])
        self.assertIn(abs(seq1 - seq2), [1])  # Should differ by 1

    def test_student_str_representation(self):
        """Test string representation of student."""
        student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            gender='M',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='GH901234I',
            phone_number='+254745678901',
            email='test@example.com',
            address='999 Test Road, Nairobi',
            created_by=self.user
        )

        expected = f"{student.student_id} - Test Student"
        self.assertEqual(str(student), expected)

    def test_student_validation_national_id_duplicate(self):
        """Test that duplicate national ID/passport raises validation error."""
        Student.objects.create(
            first_name='First',
            last_name='Student',
            gender='M',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='DUP123456J',
            phone_number='+254756789012',
            email='first@example.com',
            address='111 First Street, Nairobi',
            created_by=self.user
        )

        # Try to create another student with same national ID
        with self.assertRaises(ValidationError):
            duplicate_student = Student(
                first_name='Second',
                last_name='Student',
                gender='F',
                date_of_birth=datetime.date(2001, 1, 1),
                nationality='KE',
                national_id_passport='DUP123456J',  # Duplicate!
                phone_number='+254767890123',
                email='second@example.com',
                address='222 Second Avenue, Nairobi',
                created_by=self.user
            )
            duplicate_student.full_clean()  # This triggers validation

    def test_next_of_kin_relationship(self):
        """Test next of kin relationship."""
        student = Student.objects.create(
            first_name='Kin',
            last_name='Test',
            gender='F',
            date_of_birth=datetime.date(2000, 3, 15),
            nationality='KE',
            national_id_passport='KIN987654L',
            phone_number='+254778901234',
            email='kin@example.com',
            address='333 Kin Boulevard, Nairobi',
            next_of_kin=self.next_of_kin,
            created_by=self.user
        )

        self.assertEqual(student.next_of_kin, self.next_of_kin)
        self.assertIn(student, self.next_of_kin.students.all())

    def test_student_status_choices(self):
        """Test that student status choices work correctly."""
        for status_choice, _ in Student.STATUS_CHOICES:
            student = Student.objects.create(
                first_name=f'Status{status_choice.title()}',
                last_name='Test',
                gender='M',
                date_of_birth=datetime.date(2000, 1, 1),
                nationality='KE',
                national_id_passport=f'STAT{status_choice.upper()}123',
                phone_number=f'+254789012{status_choice[:3]}',
                email=f'status{status_choice}@example.com',
                address=f'{status_choice.title()} Street, Nairobi',
                status=status_choice,
                created_by=self.user
            )
            self.assertEqual(student.status, status_choice)


class NextOfKinModelTestCase(TestCase):
    """Test case for NextOfKin model."""

    def setUp(self):
        """Set up test data."""
        self.next_of_kin = NextOfKin.objects.create(
            first_name='Emergency',
            last_name='Contact',
            relationship='Mother',
            phone_number='+254700000000',
            email='emergency@example.com',
            address='444 Emergency Lane, Nairobi'
        )

    def test_next_of_kin_creation(self):
        """Test that next of kin can be created."""
        self.assertEqual(self.next_of_kin.first_name, 'Emergency')
        self.assertEqual(self.next_of_kin.last_name, 'Contact')
        self.assertEqual(self.next_of_kin.relationship, 'Mother')
        self.assertEqual(self.next_of_kin.__str__(), 'Emergency Contact (Mother)')

    def test_next_of_kin_str_representation(self):
        """Test string representation."""
        expected = 'Emergency Contact (Mother)'
        self.assertEqual(str(self.next_of_kin), expected)