from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.courses.models import Class  # Class model is defined in courses app
from .serializers import ClassSerializer, ClassDetailSerializer
from apps.courses.models import Course
from apps.students.models import Student
from apps.accounts.models import User


class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing classes.
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'status', 'is_active']
    search_fields = ['name', 'course__name', 'course__course_code']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'name']
    ordering = ['-start_date']

    def get_queryset(self):
        """
        Optionally restricts the returned classes based on query parameters.
        """
        queryset = Class.objects.select_related(
            'course', 'course__category', 'created_by', 'updated_by'
        ).prefetch_related('enrollments__student')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        # Filter by course if provided
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        # Filter by tutor (instructor) if provided
        tutor_id = self.request.query_params.get('tutor_id')
        if tutor_id:
            # Assuming tutor is a user with tutor role teaching this class
            # This would need to be implemented based on how tutor assignment works
            pass

        return queryset

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user.
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Set the updated_by field to the current user.
        """
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def enroll_student(self, request, pk=None):
        """
        Enroll a student in this class.
        """
        class_obj = self.get_object()
        student_id = request.data.get('student_id')

        if not student_id:
            return Response(
                {'error': 'student_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already enrolled
        if class_obj.enrollments.filter(student=student, is_active=True).exists():
            return Response(
                {'error': 'Student is already enrolled in this class'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if class is full
        if class_obj.is_full:
            return Response(
                {'error': 'Class is at maximum capacity'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create enrollment
        from apps.courses.models import Enrollment
        enrollment = Enrollment.objects.create(
            student=student,
            class_instance=class_obj,
            status='pending',
            created_by=request.user
        )

        return Response({
            'message': 'Student enrolled successfully',
            'enrollment_id': str(enrollment.id)
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def withdraw_student(self, request, pk=None):
        """
        Withdraw a student from this class.
        """
        class_obj = self.get_object()
        student_id = request.data.get('student_id')

        if not student_id:
            return Response(
                {'error': 'student_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            enrollment = class_obj.enrollments.get(
                student_id=student_id,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Student is not enrolled in this class'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update enrollment status
        enrollment.status = 'dropped'
        enrollment.is_active = False
        enrollment.updated_by = request.user
        enrollment.save()

        return Response({
            'message': 'Student withdrawn successfully'
        })

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming classes.
        """
        from datetime import date
        today = date.today()
        queryset = self.get_queryset().filter(
            start_date__gte=today,
            status__in=['planned', 'ongoing']
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get currently active classes.
        """
        queryset = self.get_queryset().filter(status='ongoing', is_active=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)