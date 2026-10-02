from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.courses.models import Course, CourseCategory
from apps.students.models import Student
import datetime

User = get_user_model()


class ClassViewSetTestCase(TestCase):
    """Test case for ClassViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.category = CourseCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )

        self.course = Course.objects.create(
            course_code='TEST-001',
            name='Test Course',
            category=self.category,
            description='Test course description',
            course_type='ielts',
            duration_weeks=12,
            duration_hours=120,
            fee=10000.00,
            registration_fee=1000.00,
            minimum_students=5,
            maximum_students=20,
            created_by=self.user
        )

        self.class_obj = self.__class__.create_test_class(
            name='Test Class',
            course=self.course,
            start_date=datetime.date(2026, 10, 1),
            end_date=datetime.date(2026, 12, 20),
            status='planned',
            created_by=self.user
        )

    @staticmethod
    def create_test_class(name, course, start_date, end_date, status, created_by):
        """Helper method to create a test class."""
        from apps.courses.models import Class
        return Class.objects.create(
            name=name,
            course=course,
            start_date=start_date,
            end_date=end_date,
            status=status,
            created_by=created_by
        )

    def test_list_classes(self):
        """Test retrieving a list of classes."""
        url = reverse('classes:class-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_class(self):
        """Test retrieving a specific class."""
        url = reverse('classes:class-detail', kwargs={'pk': self.class_obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.class_obj.name)

    def test_create_class(self):
        """Test creating a new class."""
        url = reverse('classes:class-list')
        data = {
            'name': 'New Test Class',
            'course_id': str(self.course.id),
            'start_date': datetime.date(2026, 11, 1),
            'end_date': datetime.date(2027, 1, 20),
            'status': 'planned'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Class.objects.count(), 2)

    def test_update_class(self):
        """Test updating a class."""
        url = reverse('classes:class-detail', kwargs={'pk': self.class_obj.pk})
        data = {
            'name': 'Updated Class Name',
            'course_id': str(self.course.id),
            'start_date': self.class_obj.start_date,
            'end_date': self.class_obj.end_date,
            'status': 'ongoing'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.class_obj.refresh_from_db()
        self.assertEqual(self.class_obj.name, 'Updated Class Name')

    def test_partial_update_class(self):
        """Test partially updating a class."""
        url = reverse('classes:class-detail', kwargs={'pk': self.class_obj.pk})
        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.class_obj.refresh_from_db()
        self.assertEqual(self.class_obj.status, 'completed')

    def test_delete_class(self):
        """Test deleting a class."""
        url = reverse('classes:class-detail', kwargs={'pk': self.class_obj.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Class.objects.count(), 0)

    def test_enroll_student(self):
        """Test enrolling a student in a class."""
        # Create a test student
        student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            gender='M',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='AB123456C',
            phone_number='+254712345678',
            email='test@example.com',
            address='123 Test Street',
            created_by=self.user
        )

        url = reverse('classes:class-enroll-student', kwargs={'pk': self.class_obj.pk})
        data = {'student_id': str(student.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('enrollment_id', response.data)

    def test_enroll_student_already_enrolled(self):
        """Test enrolling a student who is already enrolled."""
        # Create a test student
        student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            gender='M',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='AB123456C',
            phone_number='+254712345678',
            email='test@example.com',
            address='123 Test Street',
            created_by=self.user
        )

        # Create enrollment
        from apps.courses.models import Enrollment
        Enrollment.objects.create(
            student=student,
            class_instance=self.class_obj,
            status='confirmed',
            created_by=self.user
        )

        url = reverse('classes:class-enroll-student', kwargs={'pk': self.class_obj.pk})
        data = {'student_id': str(student.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_withdraw_student(self):
        """Test withdrawing a student from a class."""
        # Create a test student
        student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            gender='M',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='AB123456C',
            phone_number='+254712345678',
            email='test@example.com',
            address='123 Test Street',
            created_by=self.user
        )

        # Create enrollment
        from apps.courses.models import Enrollment
        enrollment = Enrollment.objects.create(
            student=student,
            class_instance=self.class_obj,
            status='confirmed',
            created_by=self.user
        )

        url = reverse('classes:class-withdraw-student', kwargs={'pk': self.class_obj.pk})
        data = {'student_id': str(student.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check enrollment status
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'dropped')
        self.assertFalse(enrollment.is_active)

    def test_upcoming_classes(self):
        """Test retrieving upcoming classes."""
        url = reverse('classes:class-upcoming')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include our test class which starts in the future
        self.assertGreaterEqual(len(response.data), 1)

    def test_active_classes(self):
        """Test retrieving active classes."""
        # Create an ongoing class
        ongoing_class = self.__class__.create_test_class(
            name='Ongoing Class',
            course=self.course,
            start_date=datetime.date(2026, 9, 1),
            end_date=datetime.date(2026, 10, 31),
            status='ongoing',
            created_by=self.user
        )

        url = reverse('classes:class-active')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include the ongoing class
        self.assertGreaterEqual(len(response.data), 1)