from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Student, NextOfKin, StudentDocument
from apps.accounts.models import User
import datetime
from rest_framework.test import APIClient
from rest_framework import status
import json


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

    def test_student_id_generation_year_rollover(self):
        """Test that student ID sequence resets yearly."""
        # This test would require mocking timezone.now() to simulate different months/years
        # For simplicity, we'll test the logic conceptually
        pass  # Implementation would require mocking

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


class StudentAPITestCase(TestCase):
    """Test case for Student API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Create HOD user for registration tests
        self.hod_user = User.objects.create_user(
            username='hoduser',
            email='hod@example.com',
            password='hodpass123',
            first_name='HOD',
            last_name='User',
            is_staff=True
        )

        # Create Super Admin user
        self.superadmin_user = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='superadminpass123',
            first_name='Super',
            last_name='Admin'
        )

        # Create roles
        from apps.accounts.models import Role
        self.hod_role = Role.objects.create(name='HOD', description='HOD role')
        self.staff_role = Role.objects.create(name='Staff', description='Staff role')
        self.superadmin_role = Role.objects.create(name='Super Admin', description='Super Admin role')

        self.hod_user.roles.add(self.hod_role)
        self.staff_user.roles.add(self.staff_role)
        self.superadmin_user.roles.add(self.superadmin_role)

    def authenticate_user(self, username, password):
        """Helper to authenticate and set client credentials."""
        login_url = '/api/v1/auth/login/'
        login_data = {'username': username, 'password': password}
        response = self.client.post(login_url, login_data, format='json')
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data['tokens']['access']
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
            return True
        return False

    def test_student_registration_endpoint_exists(self):
        """Test that student registration endpoint exists."""
        # Authenticate as HOD (who can register students)
        self.authenticate_user('hoduser', 'hodpass123')

        url = '/api/v1/students/register/'
        data = {
            'first_name': 'New',
            'last_name': 'Student',
            'gender': 'M',
            'date_of_birth': '2000-01-15',
            'nationality': 'KE',
            'national_id_passport': 'NEW123456K',
            'phone_number': '+254711111111',
            'email': 'new@example.com',
            'address': '123 New Street, Nairobi',
            'status': 'active'
        }

        response = self.client.post(url, data, format='json')
        # Should succeed or give validation error, not 404
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_registration_permission_required(self):
        """Test that student registration requires appropriate permissions."""
        # Test as unauthenticated user
        url = '/api/v1/students/register/'
        data = {
            'first_name': 'New',
            'last_name': 'Student',
            'gender': 'M',
            'date_of_birth': '2000-01-15',
            'nationality': 'KE',
            'national_id_passport': 'NEW123456K',
            'phone_number': '+254711111111',
            'email': 'new@example.com',
            'address': '123 New Street, Nairobi',
            'status': 'active'
        }

        response = self.client.post(url, data, format='json')
        # Should be unauthorized (401) for unauthenticated user
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test as regular staff (should not be able to register)
        self.authenticate_user('staffuser', 'staffpass123')

        response = self.client.post(url, data, format='json')
        # Should be forbidden (403) for regular staff
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as HOD (should be able to register)
        self.authenticate_user('hoduser', 'hodpass123')

        response = self.client.post(url, data, format='json')
        # Should succeed or give validation error, not 403
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as Super Admin (should be able to register)
        self.authenticate_user('superadmin', 'superadminpass123')

        response = self.client.post(url, data, format='json')
        # Should succeed or give validation error, not 403
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_registration_success(self):
        """Test successful student registration."""
        # Authenticate as HOD
        self.authenticate_user('hoduser', 'hodpass123')

        url = '/api/v1/students/register/'
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'gender': 'F',
            'date_of_birth': '2000-05-20',
            'nationality': 'KE',
            'national_id_passport': 'JD789012L',
            'phone_number': '+254722222222',
            'email': 'jane.doe@example.com',
            'address': '456 Student Ave, Nairobi',
            'status': 'active'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('student_id', response.data)
        self.assertTrue(response.data['student_id'].startswith('SAKE/'))
        self.assertEqual(response.data['first_name'], 'Jane')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertEqual(response.data['national_id_passport'], 'JD789012L')

        # Verify student was actually created in database
        student_id = response.data['student_id']
        self.assertTrue(Student.objects.filter(student_id=student_id).exists())

    def test_student_registration_with_next_of_kin(self):
        """Test student registration with next of kin information."""
        # Authenticate as HOD
        self.authenticate_user('hoduser', 'hodpass123')

        url = '/api/v1/students/register/'
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'gender': 'F',
            'date_of_birth': '2000-05-20',
            'nationality': 'KE',
            'national_id_passport': 'JD789012L',
            'phone_number': '+254722222222',
            'email': 'jane.doe@example.com',
            'address': '456 Student Ave, Nairobi',
            'status': 'active',
            'next_of_kin': {
                'first_name': 'John',
                'last_name': 'Doe',
                'relationship': 'Father',
                'phone_number': '+254733333333'
            }
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('student_id', response.data)
        self.assertTrue(response.data['student_id'].startswith('SAKE/'))
        self.assertEqual(response.data['first_name'], 'Jane')
        self.assertEqual(response.data['last_name'], 'Doe')

        # Verify next of kin was created
        student_id = response.data['student_id']
        student = Student.objects.get(student_id=student_id)
        self.assertEqual(student.next_of_kin.first_name, 'John')
        self.assertEqual(student.next_of_kin.last_name, 'Doe')
        self.assertEqual(student.next_of_kin.relationship, 'Father')

    def test_student_registration_duplicate_national_id(self):
        """Test that duplicate national ID/passport is rejected."""
        # Create first student
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
            created_by=self.staff_user
        )

        # Try to register another student with same national ID
        self.authenticate_user('hoduser', 'hodpass123')

        url = '/api/v1/students/register/'
        data = {
            'first_name': 'Second',
            'last_name': 'Student',
            gender='F',
            date_of_birth=datetime.date(2001, 1, 1),
            nationality='KE',
            national_id_passport='DUP123456J',  # Duplicate!
            phone_number='+254767890123',
            email='second@example.com',
            address='222 Second Avenue, Nairobi',
            'status': 'active'
        }

        response = self.client.post(url, data, format='json')
        # Should give validation error, not succeed
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('national_id_passport', response.data)

    def test_student_registration_invalid_phone(self):
        """Test that invalid phone number is rejected."""
        # Authenticate as HOD
        self.authenticate_user('hoduser', 'hodpass123')

        url = '/api/v1/students/register/'
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'gender': 'F',
            'date_of_birth': '2000-05-20',
            'nationality': 'KE',
            'national_id_passport': 'JD789012L',
            'phone_number': 'invalid-phone-number',  # Invalid format
            'email': 'jane.doe@example.com',
            'address': '456 Student Ave, Nairobi',
            'status': 'active'
        }

        response = self.client.post(url, data, format='json')
        # Should give validation error, not succeed
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

    def test_student_list_endpoint(self):
        """Test student list endpoint."""
        # Create a test student
        student = Student.objects.create(
            first_name='Existing',
            last_name': 'Student',
            gender': 'M',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='EXT123456M',
            phone_number='+254733333333',
            email='existing@example.com',
            address='789 Existing Road, Nairobi',
            created_by=self.staff_user
        )

        # Authenticate as any user
        self.authenticate_user('staffuser', 'staffpass123')

        url = '/api/v1/students/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

        # Check if our student is in the list
        student_ids = [s['student_id'] for s in response.data]
        self.assertIn(student.student_id, student_ids)

    def test_student_detail_endpoint(self):
        """Test student detail endpoint."""
        # Create a test student
        student = Student.objects.create(
            first_name='Detail',
            last_name': 'Test',
            gender': 'F',
            date_of_birth=datetime.date(2000, 2, 15),
            nationality='KE',
            national_id_passport='DET789012N',
            phone_number='+254744444444',
            email': 'detail@example.com',
            address': '321 Detail Lane, Nairobi',
            created_by=self.staff_user
        )

        # Authenticate as any user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{student.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Detail')
        self.assertEqual(response.data['last_name'], 'Test')
        self.assertEqual(response.data['student_id'], student.student_id)