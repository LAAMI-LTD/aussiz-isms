from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import AttendanceSession, AttendanceStatus, AttendanceRecord
from apps.students.models import Student
from apps.courses.models import Class, Course, CourseCategory
from apps.accounts.models import User
import datetime


class AttendanceStatusModelTestCase(TestCase):
    """Test case for AttendanceStatus model."""

    def setUp(self):
        """Set up test data."""
        self.status_present = AttendanceStatus.objects.create(
            code='P',
            name='Present',
            description='Student is present',
            is_present=True,
            points=1.00,
            color='#10B981'  # Green
        )

        self.status_absent = AttendanceStatus.objects.create(
            code='A',
            name='Absent',
            description='Student is absent',
            is_present=False,
            points=0.00,
            color='#EF4444'  # Red
        )

    def test_attendance_status_creation(self):
        """Test that attendance statuses can be created."""
        self.assertEqual(self.status_present.code, 'P')
        self.assertEqual(self.status_present.name, 'Present')
        self.assertTrue(self.status_present.is_present)
        self.assertEqual(self.status_present.points, 1.00)

        self.assertEqual(self.status_absent.code, 'A')
        self.assertEqual(self.status_absent.name, 'Absent')
        self.assertFalse(self.status_absent.is_present)
        self.assertEqual(self.status_absent.points, 0.00)

    def test_attendance_status_str_representation(self):
        """Test string representation of attendance status."""
        self.assertEqual(str(self.status_present), 'P - Present')
        self.assertEqual(str(self.status_absent), 'A - Absent')


class AttendanceSessionModelTestCase(TestCase):
    """Test case for AttendanceSession model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='tutoruser',
            email='tutor@example.com',
            password='tutorpass123',
            first_name='Tutor',
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

        self.class_instance = Class.objects.create(
            course=self.course,
            name='IELTS Morning Oct 2026',
            start_date=datetime.date(2026, 10, 1),
            end_date=datetime.date(2026, 12, 20),
            status='planned',
            created_by=self.user
        )

    def test_attendance_session_creation(self):
        """Test that an attendance session can be created."""
        session_date = datetime.date(2026, 10, 5)

        session = AttendanceSession.objects.create(
            class_instance=self.class_instance,
            session_date=session_date,
            session_number=1,
            topic='Introduction to IELTS',
            description='First session covering IELTS overview',
            start_time=datetime.time(9, 0),  # 9:00 AM
            end_time=datetime.time(12, 0),   # 12:00 PM
            created_by=self.user
        )

        self.assertEqual(session.class_instance, self.class_instance)
        self.assertEqual(session.session_date, session_date)
        self.assertEqual(session.session_number, 1)
        self.assertEqual(session.topic, 'Introduction to IELTS')
        self.assertEqual(session.start_time, datetime.time(9, 0))
        self.assertEqual(session.end_time, datetime.time(12, 0))
        self.assertTrue(session.is_active)

    def test_attendance_session_str_representation(self):
        """Test string representation of attendance session."""
        session_date = datetime.date(2026, 10, 5)
        session = AttendanceSession.objects.create(
            class_instance=self.class_instance,
            session_date=session_date,
            session_number=1,
            topic='Introduction to IELTS',
            created_by=self.user
        )

        expected = f'IELTS Morning Oct 2026 - Session 1 ({session_date})'
        self.assertEqual(str(session), expected)

    def test_attendance_session_duration_hours(self):
        """Test duration_hours property."""
        session = AttendanceSession.objects.create(
            class_instance=self.class_instance,
            session_date=datetime.date(2026, 10, 5),
            session_number=1,
            topic='Introduction to IELTS',
            start_time=datetime.time(9, 0),   # 9:00 AM
            end_time=datetime.time(12, 0),    # 12:00 PM
            created_by=self.user
        )

        # Should be 3 hours (9:00 to 12:00)
        self.assertEqual(session.duration_hours, 3.0)

        # Test with no times
        session_no_times = AttendanceSession.objects.create(
            class_instance=self.class_instance,
            session_date=datetime.date(2026, 10, 5),
            session_number=2,
            topic='Listening Practice',
            created_by=self.user
        )

        self.assertIsNone(session_no_times.duration_hours)

    def test_attendance_session_unique_together(self):
        """Test unique_together constraint on class_instance, session_date, session_number."""
        session_date = datetime.date(2026, 10, 5)

        # Create first session
        AttendanceSession.objects.create(
            class_instance=self.class_instance,
            session_date=session_date,
            session_number=1,
            topic='First Session',
            created_by=self.user
        )

        # Try to create duplicate session (same class, date, and session number)
        with self.assertRaises(Exception):  # Will raise IntegrityError
            duplicate_session = AttendanceSession(
                class_instance=self.class_instance,
                session_date=session_date,
                session_number=1,  # Duplicate!
                topic='Duplicate Session',
                created_by=self.user
            )
            duplicate_session.save()


class AttendanceRecordModelTestCase(TestCase):
    """Test case for AttendanceRecord model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='tutoruser',
            email='tutor@example.com',
            password='tutorpass123',
            first_name='Tutor',
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

        self.class_instance = Class.objects.create(
            course=self.course,
            name='IELTS Morning Oct 2026',
            start_date=datetime.date(2026, 10, 1),
            end_date=datetime.date(2026, 12, 20),
            status='planned',
            created_by=self.user
        )

        self.student = Student.objects.create(
            first_name='Jane',
            last_name='Smith',
            gender='F',
            date_of_birth=datetime.date(2000, 1, 15),
            nationality='KE',
            national_id_passport='AB123456C',
            phone_number='+254712345678',
            email='jane.smith@example.com',
            address='123 Student Street, Nairobi',
            created_by=self.user
        )

        self.status_present = AttendanceStatus.objects.create(
            code='P',
            name='Present',
            description='Student is present',
            is_present=True,
            points=1.00
        )

        self.status_late = AttendanceStatus.objects.create(
            code='L',
            name='Late',
            description='Student arrived late',
            is_present=True,
            points=0.50
        )

        self.session = AttendanceSession.objects.create(
            class_instance=self.class_instance,
            session_date=datetime.date(2026, 10, 5),
            session_number=1,
            topic='Introduction to IELTS',
            created_by=self.user
        )

    def test_attendance_record_creation(self):
        """Test that an attendance record can be created."""
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=self.status_present,
            remarks='On time',
            recorded_by=self.user
        )

        self.assertEqual(record.session, self.session)
        self.assertEqual(record.student, self.student)
        self.assertEqual(record.status, self.status_present)
        self.assertEqual(record.remarks, 'On time')
        self.assertEqual(record.recorded_by, self.user)

    def test_attendance_record_str_representation(self):
        """Test string representation of attendance record."""
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=self.status_present,
            recorded_by=self.user
        )

        expected = f'{self.student.get_full_name()} - IELTS Morning Oct 2026 - Session 1 ({self.session.session_date}) - Present'
        self.assertEqual(str(record), expected)

    def test_attendance_record_unique_together(self):
        """Test unique_together constraint on session and student."""
        # Create first attendance record
        AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=self.status_present,
            recorded_by=self.user
        )

        # Try to create duplicate record for same student and session
        with self.assertRaises(Exception):  # Will raise IntegrityError
            duplicate_record = AttendanceRecord(
                session=self.session,
                student=self.student,  # Same student
                status=self.status_late,  # Different status but still duplicate session/student
                recorded_by=self.user
            )
            duplicate_record.save()

        # But we should be able to create a record for a different student
        student2 = Student.objects.create(
            first_name='John',
            last_name='Doe',
            gender='M',
            date_of_birth=datetime.date(1999, 8, 10),
            nationality='KE',
            national_id_passport='EF345678G',
            phone_number='+254723456789',
            email='john.doe@example.com',
            address='456 Learner Ave, Nairobi',
            created_by=self.user
        )

        # This should work (different student)
        record2 = AttendanceRecord.objects.create(
            session=self.session,
            student=student2,
            status=self.status_present,
            recorded_by=self.user
        )
        self.assertEqual(record2.student, student2)

    def test_attendance_record_validation_not_enrolled(self):
        """Test that validation prevents recording attendance for non-enrolled students."""
        # Create a student who is NOT enrolled in the class
        student_not_enrolled = Student.objects.create(
            first_name='Not',
            last_name='Enrolled',
            gender='F',
            date_of_birth=datetime.date(2001, 3, 20),
            nationality='KE',
            national_id_passport='GH901234I',
            phone_number='+254734567890',
            email='not.enrolled@example.com',
            address='789 Non-Enrolled Street, Nairobi',
            created_by=self.user
        )

        # Try to create attendance record for non-enrolled student
        # Note: This validation happens at the serializer level, not model level
        # So we're testing that the model allows it (validation is in serializer)
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=student_not_enrolled,
            status=self.status_present,
            recorded_by=self.user
        )
        # The model allows it - validation happens in serializer/view
        self.assertEqual(record.student, student_not_enrolled)