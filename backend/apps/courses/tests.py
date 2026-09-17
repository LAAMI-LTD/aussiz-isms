from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import CourseCategory, Course, Class
from apps.accounts.models import User
import datetime


class CourseCategoryModelTestCase(TestCase):
    """Test case for CourseCategory model."""

    def setUp(self):
        """Set up test data."""
        self.category = CourseCategory.objects.create(
            name='Language Preparation',
            description='Courses for language exam preparation'
        )

    def test_category_creation(self):
        """Test that a course category can be created."""
        self.assertEqual(self.category.name, 'Language Preparation')
        self.assertEqual(self.category.description, 'Courses for language exam preparation')

    def test_category_str_representation(self):
        """Test string representation of category."""
        self.assertEqual(str(self.category), 'Language Preparation')


class CourseModelTestCase(TestCase):
    """Test case for Course model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )

        self.category = CourseCategory.objects.create(
            name='Language Preparation',
            description='Courses for language exam preparation'
        )

    def test_course_creation(self):
        """Test that a course can be created with valid data."""
        course = Course.objects.create(
            course_code='IELTS-001',
            name='IELTS Preparation Course',
            category=self.category,
            description='Comprehensive IELTS preparation course covering all four modules',
            course_type='ielts',
            duration_weeks=12,
            duration_hours=120,
            delivery_mode='in_person',
            fee=15000.00,
            registration_fee=2000.00,
            minimum_students=5,
            maximum_students=20,
            status='active',
            created_by=self.user
        )

        self.assertEqual(course.course_code, 'IELTS-001')
        self.assertEqual(course.name, 'IELTS Preparation Course')
        self.assertEqual(course.category, self.category)
        self.assertEqual(course.course_type, 'ielts')
        self.assertEqual(course.duration_weeks, 12)
        self.assertEqual(course.duration_hours, 120)
        self.assertEqual(course.fee, 15000.00)
        self.assertEqual(course.registration_fee, 2000.00)
        self.assertEqual(course.minimum_students, 5)
        self.assertEqual(course.maximum_students, 20)
        self.assertEqual(course.status, 'active')
        self.assertTrue(course.is_active)

    def test_course_str_representation(self):
        """Test string representation of course."""
        course = Course.objects.create(
            course_code='IELTS-001',
            name='IELTS Preparation Course',
            category=self.category,
            description='Test course',
            course_type='ielts',
            duration_weeks=12,
            duration_hours=120,
            delivery_mode='in_person',
            fee=15000.00,
            registration_fee=2000.00,
            minimum_students=5,
            maximum_students=20,
            created_by=self.user
        )

        expected = 'IELTS-001 - IELTS Preparation Course'
        self.assertEqual(str(course), expected)

    def test_course_validation_duplicate_code(self):
        """Test that duplicate course code raises validation error."""
        Course.objects.create(
            course_code='DUP-001',
            name='First Course',
            category=self.category,
            description='First test course',
            course_type='ielts',
            duration_weeks=12,
            duration_hours=120,
            delivery_mode='in_person',
            fee=15000.00,
            registration_fee=2000.00,
            minimum_students=5,
            maximum_students=20,
            created_by=self.user
        )

        # Try to create another course with same course code
        with self.assertRaises(ValidationError):
            duplicate_course = Course(
                course_code='DUP-001',  # Duplicate!
                name='Second Course',
                category=self.category,
                description='Second test course',
                course_type='ielts',
                duration_weeks=12,
                duration_hours=120,
                delivery_mode='in_person',
                fee=15000.00,
                registration_fee=2000.00,
                minimum_students=5,
                maximum_students=20,
                created_by=self.user
            )
            duplicate_course.full_clean()  # This triggers validation

    def test_course_validation_min_max_students(self):
        """Test validation for minimum and maximum students."""
        # Test valid case: min <= max
        try:
            valid_course = Course(
                course_code='VALID-001',
                name='Valid Course',
                category=self.category,
                description='Valid test course',
                course_type='ielts',
                duration_weeks=12,
                duration_hours=120,
                delivery_mode='in_person',
                fee=15000.00,
                registration_fee=2000.00,
                minimum_students=5,
                maximum_students=20,
                created_by=self.user
            )
            valid_course.full_clean()  # Should not raise validation error
        except ValidationError:
            self.fail("Valid course validation failed unexpectedly")

        # Test invalid case: min > max
        with self.assertRaises(ValidationError):
            invalid_course = Course(
                course_code='INVALID-001',
                name='Invalid Course',
                category=self.category,
                description='Invalid test course',
                course_type='ielts',
                duration_weeks=12,
                duration_hours=120,
                delivery_mode='in_person',
                fee=15000.00,
                registration_fee=2000.00,
                minimum_students=25,  # Greater than max
                maximum_students=20,
                created_by=self.user
            )
            invalid_course.full_clean()  # Should raise validation error


class ClassModelTestCase(TestCase):
    """Test case for Class model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            first_name='Staff',
            last_name='User'
        )

        self.category = CourseCategory.objects.create(
            name='Language Preparation',
            description='Courses for language exam preparation'
        )

        self.course = Course.objects.create(
            course_code='IELTS-001',
            name='IELTS Preparation Course',
            category=self.category,
            description='Test IELTS course',
            course_type='ielts',
            duration_weeks=12,
            duration_hours=120,
            delivery_mode='in_person',
            fee=15000.00,
            registration_fee=2000.00,
            minimum_students=5,
            maximum_students=20,
            created_by=self.user
        )

    def test_class_creation(self):
        """Test that a class can be created with valid data."""
        start_date = datetime.date(2026, 10, 1)
        end_date = datetime.date(2026, 12, 20)

        class_obj = Class.objects.create(
            course=self.course,
            name='IELTS Morning Oct 2026',
            start_date=start_date,
            end_date=end_date,
            status='planned',
            is_active=True,
            created_by=self.user
        )

        self.assertEqual(class_obj.course, self.course)
        self.assertEqual(class_obj.name, 'IELTS Morning Oct 2026')
        self.assertEqual(class_obj.start_date, start_date)
        self.assertEqual(class_obj.end_date, end_date)
        self.assertEqual(class_obj.status, 'planned')
        self.assertTrue(class_obj.is_active)

    def test_class_str_representation(self):
        """Test string representation of class."""
        start_date = datetime.date(2026, 10, 1)
        class_obj = Class.objects.create(
            course=self.course,
            name='IELTS Morning Oct 2026',
            start_date=start_date,
            status='planned',
            created_by=self.user
        )

        expected = f'IELTS-001 - IELTS Morning Oct 2026 ({start_date})'
        self.assertEqual(str(class_obj), expected)

    def test_class_validation_date_order(self):
        """Test validation for start and end dates."""
        start_date = datetime.date(2026, 10, 1)
        end_date = datetime.date(2026, 9, 20)  # Before start date

        # Test invalid case: end_date before start_date
        with self.assertRaises(ValidationError):
            invalid_class = Class(
                course=self.course,
                name='Invalid Date Class',
                start_date=start_date,
                end_date=end_date,  # Invalid: before start_date
                status='planned',
                created_by=self.user
            )
            invalid_class.full_clean()  # Should raise validation error

        # Test valid case: end_date after start_date
        valid_end_date = datetime.date(2026, 12, 20)
        try:
            valid_class = Class(
                course=self.course,
                name='Valid Date Class',
                start_date=start_date,
                end_date=valid_end_date,  # Valid: after start_date
                status='planned',
                created_by=self.user
            )
            valid_class.full_clean()  # Should not raise validation error
        except ValidationError:
            self.fail("Valid class date validation failed unexpectedly")

    def test_class_properties(self):
        """Test class properties like duration_days, student_count, etc."""
        start_date = datetime.date(2026, 10, 1)
        end_date = datetime.date(2026, 12, 20)

        class_obj = Class.objects.create(
            course=self.course,
            name='Property Test Class',
            start_date=start_date,
            end_date=end_date,
            status='planned',
            created_by=self.user
        )

        # Test duration_days property
        expected_duration = (end_date - start_date).days + 1
        self.assertEqual(class_obj.duration_days, expected_duration)

        # Initially student_count should be 0
        self.assertEqual(class_obj.student_count, 0)

        # Initially is_full should be False (0 < max_students)
        self.assertFalse(class_obj.is_full)

        # Available spots should equal max_students
        self.assertEqual(class_obj.available_spots, self.course.maximum_students)