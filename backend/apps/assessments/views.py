from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Assessment, PracticeTest, MockTest, TestScore, AssessmentAttempt, ComponentScore, TargetBand
from .serializers import (
    AssessmentSerializer, PracticeTestSerializer, MockTestSerializer,
    TestScoreSerializer, AssessmentAttemptSerializer, ComponentScoreSerializer,
    TargetBandSerializer
)
from apps.students.models import Student
from apps.courses.models import Course, Class
from apps.accounts.models import User


class AssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing assessments.
    """
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assessment_type', 'course', 'class_instance', 'is_active', 'is_available']
    search_fields = ['name', 'description', 'course__name']
    ordering_fields = ['scheduled_date', 'start_time', 'created_at', 'name']
    ordering = ['-scheduled_date', 'start_time']

    def get_queryset(self):
        """
        Optionally restricts the returned assessments based on query parameters.
        """
        queryset = Assessment.objects.select_related(
            'course', 'class_instance', 'created_by', 'updated_by'
        ).prefetch_related('test_scores')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)

        # Filter by student if provided (to see assessments for a specific student)
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(
                assessmentattempts__student_id=student_id
            ).distinct()

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
    def start_attempt(self, request, pk=None):
        """
        Start a new attempt at this assessment.
        """
        assessment = self.get_object()
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

        # Check if assessment is available
        if not assessment.is_available:
            return Response(
                {'error': 'Assessment is not available for attempts'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determine next attempt number for this student
        last_attempt = AssessmentAttempt.objects.filter(
            assessment=assessment,
            student=student
        ).order_by('-attempt_number').first()

        attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1

        # Create attempt
        attempt = AssessmentAttempt.objects.create(
            assessment=assessment,
            student=student,
            attempt_number=attempt_number,
            status='started',
            started_at=timezone.now(),
            created_by=request.user
        )

        return Response({
            'message': 'Assessment attempt started successfully',
            'attempt_id': str(attempt.id),
            'attempt_number': attempt.attempt_number
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        """
        Get all attempts for this assessment.
        """
        assessment = self.get_object()
        attempts = assessment.attempts.select_related('student').order_by('-started_at')

        page = self.paginate_queryset(attempts)
        if page is not None:
            serializer = AssessmentAttemptSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AssessmentAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


class PracticeTestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing practice tests (read-only as they inherit from Assessment).
    """
    queryset = PracticeTest.objects.all()
    serializer_class = PracticeTestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'class_instance', 'is_active', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['scheduled_date', 'start_time', 'created_at']
    ordering = ['-scheduled_date', 'start_time']


class MockTestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing mock tests (read-only as they inherit from Assessment).
    """
    queryset = MockTest.objects.all()
    serializer_class = MockTestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'class_instance', 'is_active', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['scheduled_date', 'start_time', 'created_at']
    ordering = ['-scheduled_date', 'start_time']


class TestScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing test score components.
    """
    queryset = TestScore.objects.all()
    serializer_class = TestScoreSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assessment', 'component_name']
    search_fields = ['component_name']
    ordering_fields = ['assessment__name', 'component_name']
    ordering = ['assessment__name', 'component_name']

    def get_queryset(self):
        """
        Optionally restricts the returned test score components.
        """
        queryset = TestScore.objects.select_related('assessment')

        # Filter by assessment type if provided
        assessment_type = self.request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(assessment__assessment_type=assessment_type)

        return queryset


class AssessmentAttemptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing assessment attempts.
    """
    queryset = AssessmentAttempt.objects.all()
    serializer_class = AssessmentAttemptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assessment', 'student', 'status', 'is_passed']
    search_fields = ['student__first_name', 'student__last_name', 'assessment__name']
    ordering_fields = ['started_at', 'submitted_at', 'graded_at', 'percentage_score']
    ordering = ['-started_at']

    def get_queryset(self):
        """
        Optionally restricts the returned assessment attempts.
        """
        queryset = AssessmentAttempt.objects.select_related(
            'assessment', 'student', 'created_by', 'updated_by'
        ).prefetch_related('component_scores__test_score')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(started_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(started_at__lte=end_date)

        # Filter by score range if provided
        min_score = self.request.query_params.get('min_score')
        max_score = self.request.query_params.get('max_score')
        if min_score:
            queryset = queryset.filter(percentage_score__gte=min_score)
        if max_score:
            queryset = queryset.filter(percentage_score__lte=max_score)

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
    def submit_attempt(self, request, pk=None):
        """
        Submit an assessment attempt for grading.
        """
        attempt = self.get_object()

        if attempt.status not in ['in_progress', 'started']:
            return Response(
                {'error': 'Assessment cannot be submitted in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt.status = 'submitted'
        attempt.submitted_at = timezone.now()
        attempt.updated_by = request.user
        attempt.save()

        return Response({
            'message': 'Assessment attempt submitted successfully'
        })

    @action(detail=True, methods=['post'])
    def grade_attempt(self, request, pk=None):
        """
        Grade an assessment attempt.
        """
        attempt = self.get_object()

        if attempt.status != 'submitted':
            return Response(
                {'error': 'Only submitted assessments can be graded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # In a real implementation, this would process component scores
        # For now, we'll accept a total score
        total_score_achieved = request.data.get('total_score_achieved')
        if total_score_achieved is None:
            return Response(
                {'error': 'total_score_achieved is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt.total_score_achieved = total_score_achieved
        attempt.status = 'graded'
        attempt.graded_at = timezone.now()
        attempt.updated_by = request.user
        attempt.save()  # This will calculate percentage and pass/fail

        return Response({
            'message': 'Assessment attempt graded successfully',
            'percentage_score': float(attempt.percentage_score) if attempt.percentage_score else None,
            'is_passed': attempt.is_passed
        })

    @action(detail=True, methods=['get'])
    def component_scores(self, request, pk=None):
        """
        Get component scores for this assessment attempt.
        """
        attempt = self.get_object()
        component_scores = attempt.component_scores.select_related('test_score')

        page = self.paginate_queryset(component_scores)
        if page is not None:
            serializer = ComponentScoreSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ComponentScoreSerializer(component_scores, many=True)
        return Response(serializer.data)


class ComponentScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing component scores.
    """
    queryset = ComponentScore.objects.all()
    serializer_class = ComponentScoreSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['attempt__assessment', 'attempt__student', 'test_score__component_name']
    search_fields = ['test_score__component_name']
    ordering_fields = ['score_achieved']
    ordering = ['-score_achieved']

    def get_queryset(self):
        """
        Optionally restricts the returned component scores.
        """
        queryset = ComponentScore.objects.select_related(
            'attempt__assessment', 'attempt__student', 'test_score'
        )

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(attempt__started_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(attempt__started_at__lte=end_date)

        return queryset


class TargetBandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student target bands.
    """
    queryset = TargetBand.objects.all()
    serializer_class = TargetBandSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student__first_name', 'student__last_name', 'overall_band_score']
    search_fields = ['student__first_name', 'student__last_name']
    ordering_fields = ['overall_band_score', 'created_at']
    ordering = ['-overall_band_score']

    def get_queryset(self):
        """
        Optionally restricts the returned target bands.
        """
        queryset = TargetBand.objects.select_related('student', 'created_by', 'updated_by')

        # Filter by student if provided
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

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