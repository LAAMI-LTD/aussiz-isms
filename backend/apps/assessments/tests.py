from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.courses.models import Course, CourseCategory
from apps.students.models import Student
from apps.accounts.models import User, Role
import datetime

User = get_user_model()


class AssessmentViewSetTestCase(TestCase):
    """Test case for AssessmentViewSet."""

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

        self.assessment = self.__class__.create_test_assessment(
            name='Test Assessment',
            assessment_type='practice',
            course=self.course,
            scheduled_date=datetime.date(2026, 10, 15),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
            duration_minutes=180,
            total_score=100,
            passing_score=60,
            created_by=self.user
        )

    @staticmethod
    def create_test_assessment(name, assessment_type, course, scheduled_date,
                              start_time, end_time, duration_minutes,
                              total_score, passing_score, created_by):
        """Helper method to create a test assessment."""
        from .models import Assessment
        return Assessment.objects.create(
            name=name,
            assessment_type=assessment_type,
            course=course,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            total_score=total_score,
            passing_score=passing_score,
            created_by=created_by
        )

    def test_list_assessments(self):
        """Test retrieving a list of assessments."""
        url = reverse('assessments:assessment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_assessment(self):
        """Test retrieving a specific assessment."""
        url = reverse('assessments:assessment-detail', kwargs={'pk': self.assessment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.assessment.name)

    def test_create_assessment(self):
        """Test creating a new assessment."""
        url = reverse('assessments:assessment-list')
        data = {
            'name': 'New Test Assessment',
            'assessment_type': 'mock',
            'course_id': str(self.course.id),
            'scheduled_date': datetime.date(2026, 11, 15),
            'start_time': datetime.time(14, 0),
            'end_time': datetime.time(17, 0),
            'duration_minutes': 180,
            'total_score': 100,
            'passing_score': 60
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Assessment.objects.count(), 2)

    def test_update_assessment(self):
        """Test updating an assessment."""
        url = reverse('assessments:assessment-detail', kwargs={'pk': self.assessment.pk})
        data = {
            'name': 'Updated Assessment Name',
            'assessment_type': self.assessment.assessment_type,
            'course_id': str(self.course.id),
            'scheduled_date': self.assessment.scheduled_date,
            'start_time': self.assessment.start_time,
            'end_time': self.assessment.end_time,
            'duration_minutes': self.assessment.duration_minutes,
            'total_score': self.assessment.total_score,
            'passing_score': self.assessment.passing_score
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.name, 'Updated Assessment Name')

    def test_filter_by_assessment_type(self):
        """Test filtering assessments by type."""
        # Create a mock test
        mock_test = self.__class__.create_test_assessment(
            name='Test Mock Test',
            assessment_type='mock',
            course=self.course,
            scheduled_date=datetime.date(2026, 10, 20),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(13, 0),
            duration_minutes=180,
            total_score=100,
            passing_score=60,
            created_by=self.user
        )

        url = reverse('assessments:assessment-list')
        response = self.client.get(url, {'assessment_type': 'practice'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return the practice test, not the mock test
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.assessment.name)

    def test_start_assessment_attempt(self):
        """Test starting an assessment attempt."""
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

        url = reverse('assessments:assessment-start-attempt', kwargs={'pk': self.assessment.pk})
        data = {'student_id': str(student.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('attempt_id', response.data)
        self.assertEqual(response.data['attempt_number'], 1)

    def test_start_assessment_attempt_unavailable(self):
        """Test starting an attempt on an unavailable assessment."""
        # Make assessment unavailable
        self.assessment.is_available = False
        self.assessment.save()

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

        url = reverse('assessments:assessment-start-attempt', kwargs={'pk': self.assessment.pk})
        data = {'student_id': str(student.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PracticeTestViewSetTestCase(TestCase):
    """Test case for PracticeTestViewSet."""

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

        self.practice_test = self.__class__.create_test_practice_test(
            name='Test Practice Test',
            course=self.course,
            scheduled_date=datetime.date(2026, 10, 15),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
            duration_minutes=180,
            total_score=100,
            passing_score=60,
            created_by=self.user
        )

    @staticmethod
    def create_test_practice_test(name, course, scheduled_date, start_time,
                                 end_time, duration_minutes, total_score,
                                 passing_score, created_by):
        """Helper method to create a test practice test."""
        from .models import PracticeTest
        return PracticeTest.objects.create(
            name=name,
            course=course,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            total_score=total_score,
            passing_score=passing_score,
            created_by=created_by
        )

    def test_list_practice_tests(self):
        """Test retrieving a list of practice tests."""
        url = reverse('assessments:practicetest-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_practice_test_inherits_from_assessment(self):
        """Test that practice test is accessible through assessment endpoint."""
        url = reverse('assessments:assessment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include practice test in the list
        self.assertGreaterEqual(len(response.data['results']), 1)


class MockTestViewSetTestCase(TestCase):
    """Test case for MockTestViewSet."""

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

        self.mock_test = self.__class__.create_test_mock_test(
            name='Test Mock Test',
            course=self.course,
            scheduled_date=datetime.date(2026, 10, 15),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
            duration_minutes=180,
            total_score=100,
            passing_score=60,
            created_by=self.user
        )

    @staticmethod
    def create_test_mock_test(name, course, scheduled_date, start_time,
                             end_time, duration_minutes, total_score,
                             passing_score, created_by):
        """Helper method to create a test mock test."""
        from .models import MockTest
        return MockTest.objects.create(
            name=name,
            course=course,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            total_score=total_score,
            passing_score=passing_score,
            created_by=created_by
        )

    def test_list_mock_tests(self):
        """Test retrieving a list of mock tests."""
        url = reverse('assessments:mocktest-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_mock_test_inherits_from_assessment(self):
        """Test that mock test is accessible through assessment endpoint."""
        url = reverse('assessments:assessment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include mock test in the list
        self.assertGreaterEqual(len(response.data['results']), 1)


class AssessmentAttemptViewSetTestCase(TestCase):
    """Test case for AssessmentAttemptViewSet."""

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

        self.assessment = self.__class__.create_test_assessment(
            name='Test Assessment',
            assessment_type='practice',
            course=self.course,
            scheduled_date=datetime.date(2026, 10, 15),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
            duration_minutes=180,
            total_score=100,
            passing_score=60,
            created_by=self.user
        )

        self.student = Student.objects.create(
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

    @staticmethod
    def create_test_assessment(name, assessment_type, course, scheduled_date,
                              start_time, end_time, duration_minutes,
                              total_score, passing_score, created_by):
        """Helper method to create a test assessment."""
        from .models import Assessment
        return Assessment.objects.create(
            name=name,
            assessment_type=assessment_type,
            course=course,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            total_score=total_score,
            passing_score=passing_score,
            created_by=created_by
        )

    def test_list_attempts(self):
        """Test retrieving a list of assessment attempts."""
        url = reverse('assessments:assessmentattempt-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # No attempts yet

    def test_create_attempt(self):
        """Test creating a new assessment attempt."""
        url = reverse('assessments:assessmentattempt-list')
        data = {
            'assessment_id': str(self.assessment.id),
            'student_id': str(self.student.id),
            'attempt_number': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AssessmentAttempt.objects.count(), 1)

    def test_retrieve_attempt(self):
        """Test retrieving a specific assessment attempt."""
        # Create an attempt first
        attempt = AssessmentAttempt.objects.create(
            assessment=self.assessment,
            student=self.student,
            attempt_number=1,
            started_at=datetime.datetime(2026, 10, 15, 9, 0, 0),
            created_by=self.user
        )

        url = reverse('assessments:assessmentattempt-detail', kwargs={'pk': attempt.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student']['first_name'], self.student.first_name)
        self.assertEqual(response.data['assessment']['name'], self.assessment.name)

    def test_submit_attempt(self):
        """Test submitting an assessment attempt."""
        # Create an attempt
        attempt = AssessmentAttempt.objects.create(
            assessment=self.assessment,
            student=self.student,
            attempt_number=1,
            status='in_progress',
            created_by=self.user
        )

        url = reverse('assessments:assessmentattempt-submit-attempt', kwargs={'pk': attempt.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that status was updated
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'submitted')
        self.assertIsNotNone(attempt.submitted_at)

    def test_grade_attempt(self):
        """Test grading an assessment attempt."""
        # Create a submitted attempt
        attempt = AssessmentAttempt.objects.create(
            assessment=self.assessment,
            student=self.student,
            attempt_number=1,
            status='submitted',
            created_by=self.user
        )

        url = reverse('assessments:assessmentattempt-grade-attempt', kwargs={'pk': attempt.pk})
        data = {'total_score_achieved': 75}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that attempt was graded
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'graded')
        self.assertEqual(attempt.total_score_achieved, 75)
        self.assertEqual(attempt.percentage_score, 75.00)  # 75/100 * 100
        self.assertTrue(attempt.is_passed)  # 75 >= 60 passing score

    def test_grade_attempt_fail(self):
        """Test grading an assessment attempt that fails."""
        # Create a submitted attempt
        attempt = AssessmentAttempt.objects.create(
            assessment=self.assessment,
            student=self.student,
            attempt_number=1,
            status='submitted',
            created_by=self.user
        )

        url = reverse('assessments:assessmentattempt-grade-attempt', kwargs={'pk': attempt.pk})
        data = {'total_score_achieved': 45}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that attempt was graded but failed
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'graded')
        self.assertEqual(attempt.total_score_achieved, 45)
        self.assertEqual(attempt.percentage_score, 45.00)  # 45/100 * 100
        self.assertFalse(attempt.is_passed)  # 45 < 60 passing score

    def test_get_component_scores(self):
        """Test getting component scores for an assessment attempt."""
        # Create an attempt
        attempt = AssessmentAttempt.objects.create(
            assessment=self.assessment,
            student=self.student,
            attempt_number=1,
            status='completed',
            created_by=self.user
        )

        # Create a test score component
        from .models import TestScore
        test_score = TestScore.objects.create(
            assessment=self.assessment,
            component_name='Listening',
            max_score=40,
            weight=0.25
        )

        # Create a component score
        from .models import ComponentScore
        component_score = ComponentScore.objects.create(
            attempt=attempt,
            test_score=test_score,
            score_achieved=30
        )

        url = reverse('assessments:assessmentattempt-component-scores', kwargs={'pk': attempt.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['score_achieved'], 30)
        self.assertEqual(float(response.data[0]['percentage_score']), 75.00)  # 30/40 * 100


class TestScoreViewSetTestCase(TestCase):
    """Test case for TestScoreViewSet."""

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

        self.assessment = self.__class__.create_test_assessment(
            name='Test Assessment',
            assessment_type='practice',
            course=self.course,
            scheduled_date=datetime.date(2026, 10, 15),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
            duration_minutes=180,
            total_score=100,
            passing_score=60,
            created_by=self.user
        )

        self.test_score = self.__class__.create_test_test_score(
            assessment=self.assessment,
            component_name='Listening',
            max_score=40,
            weight=0.25
        )

    @staticmethod
    def create_test_assessment(name, assessment_type, course, scheduled_date,
                              start_time, end_time, duration_minutes,
                              total_score, passing_score, created_by):
        """Helper method to create a test assessment."""
        from .models import Assessment
        return Assessment.objects.create(
            name=name,
            assessment_type=assessment_type,
            course=course,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            total_score=total_score,
            passing_score=passing_score,
            created_by=created_by
        )

    @staticmethod
    def create_test_test_score(assessment, component_name, max_score, weight):
        """Helper method to create a test test score."""
        from .models import TestScore
        return TestScore.objects.create(
            assessment=assessment,
            component_name=component_name,
            max_score=max_score,
            weight=weight
        )

    def test_list_test_scores(self):
        """Test retrieving a list of test score components."""
        url = reverse('assessments:testscore-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_test_score(self):
        """Test retrieving a specific test score component."""
        url = reverse('assessments:testscore-detail', kwargs={'pk': self.test_score.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['component_name'], self.test_score.component_name)

    def test_filter_by_assessment(self):
        """Test filtering test scores by assessment."""
        # Create another assessment
        assessment2 = self.__class__.create_test_assessment(
            name='Test Assessment 2',
            assessment_type='mock',
            course=self.course,
            scheduled_date=datetime.date(2026, 11, 15),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(17, 0),
            duration_minutes=180,
            total_score=100,
            passing_score=60,
            created_by=self.user
        )

        # Create test score for second assessment
        from .models import TestScore
        test_score2 = TestScore.objects.create(
            assessment=assessment2,
            component_name='Reading',
            max_score=30,
            weight=0.30
        )

        url = reverse('assessments:testscore-list')
        response = self.client.get(url, {'assessment_id': str(self.assessment.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return test scores for the first assessment
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['component_name'], self.test_score.component_name)


class TargetBandViewSetTestCase(TestCase):
    """Test case for TargetBandViewSet."""

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

        self.target_band = self.__class__.create_test_target_band(
            student=self.student,
            overall_band_score=7.5,
            listening_target=8.0,
            reading_target=7.0,
            writing_target=7.5,
            speaking_target=7.5,
            created_by=self.user
        )

    @staticmethod
    def create_test_target_band(student, overall_band_score, listening_target,
                               reading_target, writing_target, speaking_target, created_by):
        """Helper method to create a test target band."""
        from .models import TargetBand
        return TargetBand.objects.create(
            student=student,
            overall_band_score=overall_band_score,
            listening_target=listening_target,
            reading_target=reading_target,
            writing_target=writing_target,
            speaking_target=speaking_target,
            created_by=created_by
        )

    def test_list_target_bands(self):
        """Test retrieving a list of target bands."""
        url = reverse('assessments:targetband-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_target_band(self):
        """Test retrieving a specific target band."""
        url = reverse('assessments:targetband-detail', kwargs={'pk': self.target_band.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['overall_band_score'], 7.5)

    def test_create_target_band(self):
        """Test creating a new target band."""
        # Create another student
        student2 = Student.objects.create(
            first_name='Test2',
            last_name='Student2',
            gender='F',
            date_of_birth=datetime.date(2001, 5, 15),
            nationality='KE',
            national_id_passport='AB123456D',
            phone_number='+254723456789',
            email='test2@example.com',
            address='456 Test Avenue',
            created_by=self.user
        )

        url = reverse('assessments:targetband-list')
        data = {
            'student_id': str(student2.id),
            'overall_band_score': 6.5,
            'listening_target': 7.0,
            'reading_target': 6.0,
            'writing_target': 6.5,
            'speaking_target': 6.5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TargetBand.objects.count(), 2)

    def test_update_target_band(self):
        """Test updating a target band."""
        url = reverse('assessments:targetband-detail', kwargs={'pk': self.target_band.pk})
        data = {
            'student_id': str(self.student.id),
            'overall_band_score': 8.0,
            'listening_target': self.target_band.listening_target,
            'reading_target': self.target_band.reading_target,
            'writing_target': self.target_band.writing_target,
            'speaking_target': self.target_band.speaking_target
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_band.refresh_from_db()
        self.assertEqual(self.target_band.overall_band_score, 8.0)

    def test_target_band_score_validation(self):
        """Test validation of target band scores."""
        # Test invalid overall band score (too high)
        url = reverse('assessments:targetband-list')
        data = {
            'student_id': str(self.student.id),
            'overall_band_score': 15.0,  # Invalid - over 9.0
            'listening_target': 7.0,
            'reading_target': 6.0,
            'writing_target': 6.5,
            'speaking_target': 6.5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid overall band score (too low)
        data['overall_band_score'] = -1.0  # Invalid - under 0.0
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test valid scores
        data['overall_band_score'] = 7.5
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)