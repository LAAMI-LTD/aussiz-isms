from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone
from .models import IELTSResult, IELTSResultVerification, IELTSResultAudit
from .serializers import (
    IELTSResultSerializer,
    IELTSResultVerificationSerializer,
    IELTSResultAuditSerializer
)
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest


class IELTSResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS results.
    """
    queryset = IELTSResult.objects.all()
    serializer_class = IELTSResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'student', 'test', 'result_status', 'is_verified', 'is_active'
    ]
    search_fields = [
        'student__first_name',
        'student__last_name',
        'student__student_id',
        'result_id',
        'test__title'
    ]
    ordering_fields = [
        'overall_band_score', 'release_date', 'created_at', 'expiry_date'
    ]
    ordering = ['-release_date', '-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned results based on query parameters.
        """
        queryset = IELTSResult.objects.select_related(
            'student',
            'student__user',
            'test',
            'attempt',
            'attempt__student',
            'created_by',
            'updated_by',
            'last_verified_by'
        )

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(release_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(release_date__date__lte=end_date)

        # Filter by band score range
        min_overall = self.request.query_params.get('min_overall_band')
        max_overall = self.request.query_params.get('max_overall_band')
        if min_overall:
            try:
                min_overall = float(min_overall)
                queryset = queryset.filter(overall_band_score__gte=min_overall)
            except ValueError:
                pass
        if max_overall:
            try:
                max_overall = float(max_overall)
                queryset = queryset.filter(overall_band_score__lte=max_overall)
            except ValueError:
                pass

        # Filter by expiry status
        expiry_filter = self.request.query_params.get('expired')
        if expiry_filter is not None:
            now = timezone.now().date()
            if expiry_filter.lower() == 'true':
                queryset = queryset.filter(expiry_date__lt=now)
            elif expiry_filter.lower() == 'false':
                queryset = queryset.filter(expiry_date__gte=now) | queryset.filter(expiry_date__isnull=True)

        # Filter by verification status
        verified = self.request.query_params.get('verified')
        if verified is not None:
            if verified.lower() == 'true':
                queryset = queryset.filter(is_verified=True)
            elif verified.lower() == 'false':
                queryset = queryset.filter(is_verified=False)

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
    def release(self, request, pk=None):
        """
        Release a pending result.
        """
        result = self.get_object()
        if result.result_status != 'pending':
            return Response(
                {'error': 'Only pending results can be released.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result.result_status = 'released'
        result.release_date = timezone.now()
        result.updated_by = request.user
        result.save()

        return Response({'status': 'result released'})

    @action(detail=True, methods=['post'])
    def withhold(self, request, pk=None):
        """
        Withhold a result.
        """
        result = self.get_object()
        if result.result_status == 'released':
            return Response(
                {'error': 'Released results cannot be withheld. Cancel instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result.result_status = 'withheld'
        result.updated_by = request.user
        result.save()

        return Response({'status': 'result withheld'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a result.
        """
        result = self.get_object()
        if result.result_status == 'released':
            return Response(
                {'error': 'Released results cannot be cancelled. Use withhold instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result.result_status = 'cancelled'
        result.updated_by = request.user
        result.save()

        return Response({'status': 'result cancelled'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get result statistics.
        """
        queryset = self.get_queryset()

        # Total results
        total_results = queryset.count()

        # Results by status
        status_counts = queryset.values('result_status').annotate(count=models.Count('id'))
        status_dict = {item['result_status']: item['count'] for item in status_counts}

        # Results by verification status
        verified_count = queryset.filter(is_verified=True).count()
        unverified_count = queryset.filter(is_verified=False).count()

        # Average band score
        avg_overall = queryset.aggregate(avg=models.Avg('overall_band_score'))['avg'] or 0

        # Results released in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_results = queryset.filter(
            release_date__gte=thirty_days_ago,
            result_status='released'
        ).count()

        data = {
            'total_results': total_results,
            'status_breakdown': status_dict,
            'verified_results': verified_count,
            'unverified_results': unverified_count,
            'average_overall_band_score': round(float(avg_overall), 1) if avg_overall else 0,
            'recent_results': recent_results
        }

        return Response(data)


class IELTSResultVerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS result verifications.
    """
    queryset = IELTSResultVerification.objects.all()
    serializer_class = IELTSResultVerificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'result', 'status', 'verification_type', 'is_active'
    ]
    search_fields = [
        'requestor_name',
        'requestor_institution',
        'requestor_email',
        'verification_reference',
        'result__result_id'
    ]
    ordering_fields = ['verification_date', 'status']
    ordering = ['-verification_date']

    def get_queryset(self):
        """
        Optionally restricts the returned verifications based on query parameters.
        """
        queryset = IELTSResultVerification.objects.select_related(
            'result',
            'result__student',
            'created_by',
            'updated_by'
        )

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(verification_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(verification_date__date__lte=end_date)

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
    def verify(self, request, pk=None):
        """
        Mark a verification as verified.
        """
        verification = self.get_object()
        if verification.status != 'pending':
            return Response(
                {'error': 'Only pending verifications can be marked as verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        verification.status = 'verified'
        verification.updated_by = request.user
        verification.save()

        return Response({'status': 'verification marked as verified'})

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """
        Mark a verification as failed.
        """
        verification = self.get_object()
        if verification.status != 'pending':
            return Response(
                {'error': 'Only pending verifications can be marked as failed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        verification.status = 'failed'
        verification.updated_by = request.user
        verification.save()

        return Response({'status': 'verification marked as failed'})


class IELTSResultAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing IELTS result audit trails (read-only).
    """
    queryset = IELTSResultAudit.objects.all()
    serializer_class = IELTSResultAuditSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['result', 'field_name', 'changed_by']
    search_fields = [
        'result__result_id',
        'field_name',
        'old_value',
        'new_value',
        'change_reason'
    ]
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']

    def get_queryset(self):
        """
        Optionally restricts the returned audit entries based on query parameters.
        """
        queryset = IELTSResultAudit.objects.select_related(
            'result',
            'result__student',
            'changed_by'
        )

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(changed_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(changed_at__date__lte=end_date)

        return queryset