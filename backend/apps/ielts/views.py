from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Avg
from .models import IELTSTest, IELTSTestSection, IELTSTestAttempt, IELTSTestSectionScore, IELTSProgress
from .serializers import (
    IELTSTestSerializer,
    IELTSTestSectionSerializer,
    IELTSTestAttemptSerializer,
    IELTSTestSectionScoreSerializer,
    IELTSProgressSerializer
)
from apps.accounts.models import User


class IELTSTestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS tests.
    """
    queryset = IELTSTest.objects.all()
    serializer_class = IELTSTestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['test_type', 'test_mode', 'is_active']
    search_fields = ['title', 'description', 'source_material']
    ordering_fields = ['title', 'created_at', 'test_type']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned tests based on query parameters.
        """
        queryset = IELTSTest.objects.select_related('created_by', 'updated_by')

        # Filter by active status if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

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


class IELTSTestSectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS test sections.
    """
    queryset = IELTSTestSection.objects.all()
    serializer_class = IELTSTestSectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['test', 'section_type', 'is_active']
    search_fields = ['test__title', 'instructions']
    ordering_fields = ['test__title', 'section_type', 'order']
    ordering = ['test__title', 'order']

    def get_queryset(self):
        """
        Optionally restricts the returned sections based on query parameters.
        """
        queryset = IELTSTestSection.objects.select_related('test', 'test__created_by', 'test__updated_by')

        # Filter by test if provided
        test_id = self.request.query_params.get('test')
        if test_id:
            queryset = queryset.filter(test_id=test_id)

        # Filter by active status if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def perform_create(self, serializer):
        """
        Set the test relationship when creating a section.
        """
        test_id = self.request.data.get('test_id')
        if test_id:
            serializer.save(test_id=test_id)
        else:
            serializer.save()


class IELTSTestAttemptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS test attempts.
    """
    queryset = IELTSTestAttempt.objects.all()
    serializer_class = IELTSTestAttemptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'test', 'status', 'is_active']
    search_fields = [
        'student__first_name',
        'student__last_name',
        'student__student_id',
        'test__title',
        'remarks'
    ]
    ordering_fields = ['started_at', 'completed_at', 'overall_band_score', 'created_at']
    ordering = ['-started_at']

    def get_queryset(self):
        """
        Optionally restricts the returned attempts based on query parameters.
        """
        queryset = IELTSTestAttempt.objects.select_related(
            'student',
            'test',
            'test__created_by',
            'test__updated_by',
            'created_by',
            'updated_by',
            'reviewed_by'
        ).prefetch_related('section_scores__section')

        # Filter by student if provided
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by test if provided
        test_id = self.request.query_params.get('test')
        if test_id:
            queryset = queryset.filter(test_id=test_id)

        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(started_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(started_at__date__lte=end_date)

        # Filter by completion status
        completion_status = self.request.query_params.get('completion_status')
        if completion_status == 'completed':
            queryset = queryset.filter(completed_at__isnull=False)
        elif completion_status == 'pending':
            queryset = queryset.filter(completed_at__isnull=True)

        # Filter by score range
        min_band = self.request.query_params.get('min_band_score')
        max_band = self.request.query_params.get('max_band_score')
        if min_band:
            queryset = queryset.filter(overall_band_score__gte=float(min_band))
        if max_band:
            queryset = queryset.filter(overall_band_score__lte=float(max_band))

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
    def complete(self, request, pk=None):
        """
        Mark an attempt as completed and calculate overall band score.
        """
        attempt = self.get_object()
        if attempt.status == 'completed':
            return Response(
                {'error': 'Attempt is already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt.status = 'completed'
        attempt.completed_at = timezone.now()

        # Calculate overall band score from section scores
        section_scores = attempt.section_scores.all()
        if section_scores:
            total_band = sum(score.band_score for score in section_scores)
            average_band = total_band / len(section_scores)
            # Round to nearest 0.5
            attempt.overall_band_score = round(average_band * 2) / 2
            attempt.overall_band_score = max(0.0, min(9.0, attempt.overall_band_score))

        attempt.updated_by = request.user
        attempt.save()

        return Response({
            'status': 'attempt completed',
            'overall_band_score': attempt.overall_band_score
        })

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """
        Mark an attempt as reviewed by a tutor.
        """
        attempt = self.get_object()
        if attempt.status not in ['completed', 'in_progress']:
            return Response(
                {'error': 'Only completed or in-progress attempts can be reviewed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt.status = 'reviewed'
        attempt.reviewed_by = request.user
        attempt.reviewed_at = timezone.now()
        attempt.updated_by = request.user
        attempt.save()

        return Response({'status': 'attempt reviewed'})

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent test attempts (last 30 days).
        """
        from datetime import datetime, timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_attempts = self.get_queryset().filter(started_at__gte=thirty_days_ago)
        page = self.paginate_queryset(recent_attempts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(recent_attempts, many=True)
        return Response(serializer.data)


class IELTSTestSectionScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS test section scores.
    """
    queryset = IELTSTestSectionScore.objects.all()
    serializer_class = IELTSTestSectionScoreSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['attempt', 'section', 'section__section_type', 'is_reviewed']
    search_fields = [
        'attempt__student__first_name',
        'attempt__student__last_name',
        'section__section_type',
        'remarks'
    ]
    ordering_fields = ['created_at', 'band_score', 'raw_score', 'percentage_score']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned section scores based on query parameters.
        """
        queryset = IELTSTestSectionScore.objects.select_related(
            'attempt',
            'attempt__student',
            'attempt__test',
            'section',
            'section__test',
            'reviewed_by',
            'created_by',
            'updated_by'
        )

        # Filter by student if provided
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(attempt__student_id=student_id)

        # Filter by test if provided
        test_id = self.request.query_params.get('test')
        if test_id:
            queryset = queryset.filter(attempt__test_id=test_id)

        # Filter by section type if provided
        section_type = self.request.query_params.get('section_type')
        if section_type:
            queryset = queryset.filter(section__section_type=section_type)

        # Filter by review status if provided
        is_reviewed = self.request.query_params.get('is_reviewed')
        if is_reviewed is not None:
            queryset = queryset.filter(is_reviewed=is_reviewed.lower() == 'true')

        # Filter by score range
        min_band = self.request.query_params.get('min_band_score')
        max_band = self.request.query_params.get('max_band_score')
        if min_band:
            queryset = queryset.filter(band_score__gte=float(min_band))
        if max_band:
            queryset = queryset.filter(band_score__lte=float(max_band))

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
    def review(self, request, pk=None):
        """
        Mark a section score as reviewed.
        """
        section_score = self.get_object()
        section_score.is_reviewed = True
        section_score.reviewed_by = request.user
        section_score.reviewed_at = timezone.now()
        section_score.updated_by = request.user
        section_score.save()

        return Response({'status': 'section score reviewed'})


class IELTSProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS progress tracking.
    """
    queryset = IELTSProgress.objects.all()
    serializer_class = IELTSProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'is_active']
    search_fields = [
        'student__first_name',
        'student__last_name',
        'student__student_id',
        'progress_notes',
        'recommended_focus'
    ]
    ordering_fields = ['target_band_score', 'current_estimated_band', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        """
        Optionally restricts the returned progress records based on query parameters.
        """
        queryset = IELTSProgress.objects.select_related(
            'student',
            'student__user',
            'created_by',
            'updated_by'
        )

        # Filter by student if provided
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by target band score range
        min_target = self.request.query_params.get('min_target_band')
        max_target = self.request.query_params.get('max_target_band')
        if min_target:
            queryset = queryset.filter(target_band_score__gte=float(min_target))
        if max_target:
            queryset = queryset.filter(target_band_score__lte=float(max_target))

        # Filter by current band score range
        min_current = self.request.query_params.get('min_current_band')
        max_current = self.request.query_params.get('max_current_band')
        if min_current:
            queryset = queryset.filter(current_estimated_band__gte=float(min_current))
        if max_current:
            queryset = queryset.filter(current_estimated_band__lte=float(max_current))

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

    @action(detail=False, methods=['get'])
    def needs_attention(self, request):
        """
        Get students who need attention (not making progress toward goals).
        """
        # Students whose current estimate is more than 0.5 below target and hasn't been updated recently
        from datetime import datetime, timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)

        needing_attention = self.get_queryset().filter(
            current_estimated_band__isnull=False,
            target_band_score__gt=models.F('current_estimated_band') + 0.5,
            updated_at__lt=thirty_days_ago
        )

        page = self.paginate_queryset(needing_attention)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(needing_attention, many=True)
        return Response(serializer.data)