from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import IELTSExamCenter, IELTSExamDate, IELTSExamBooking
from .serializers import (
    IELTSExamCenterSerializer,
    IELTSExamDateSerializer,
    IELTSExamBookingSerializer
)
from apps.students.models import Student
from apps.accounts.models import User


class IELTSExamCenterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS exam centers.
    """
    queryset = IELTSExamCenter.objects.all()
    serializer_class = IELTSExamCenterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['city', 'country', 'is_active']
    search_fields = ['name', 'address', 'city']
    ordering_fields = ['name', 'city', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """
        Optionally restricts the returned centers based on query parameters.
        """
        queryset = IELTSExamCenter.objects.select_related('created_by', 'updated_by')
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


class IELTSExamDateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS exam dates.
    """
    queryset = IELTSExamDate.objects.all()
    serializer_class = IELTSExamDateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['center', 'exam_type', 'exam_date', 'is_active']
    search_fields = ['center__name', 'center__city']
    ordering_fields = ['exam_date', 'registration_deadline', 'exam_fee']
    ordering = ['exam_date']

    def get_queryset(self):
        """
        Optionally restricts the returned exam dates based on query parameters.
        """
        queryset = IELTSExamDate.objects.select_related(
            'center', 'center__created_by', 'center__updated_by',
            'created_by', 'updated_by'
        )

        # Filter by upcoming exams only if requested
        upcoming_only = self.request.query_params.get('upcoming_only')
        if upcoming_only is not None and upcoming_only.lower() == 'true':
            queryset = queryset.filter(exam_date__gte=timezone.now().date())

        # Filter by available slots
        min_available = self.request.query_params.get('min_available_slots')
        if min_available:
            try:
                min_available = int(min_available)
                queryset = queryset.filter(available_slots__gte=min_available)
            except ValueError:
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

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming exam dates.
        """
        upcoming_dates = self.get_queryset().filter(
            exam_date__gte=timezone.now().date()
        ).order_by('exam_date')

        page = self.paginate_queryset(upcoming_dates)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(upcoming_dates, many=True)
        return Response(serializer.data)


class IELTSExamBookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing IELTS exam bookings.
    """
    queryset = IELTSExamBooking.objects.all()
    serializer_class = IELTSExamBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'exam_date', 'status', 'is_active']
    search_fields = [
        'student__first_name',
        'student__last_name',
        'student__student_id',
        'exam_date__center__name',
        'payment_reference'
    ]
    ordering_fields = ['booking_date', 'exam_date__exam_date', 'amount_paid']
    ordering = ['-booking_date']

    def get_queryset(self):
        """
        Optionally restricts the returned bookings based on query parameters.
        """
        queryset = IELTSExamBooking.objects.select_related(
            'student',
            'student__user',
            'exam_date',
            'exam_date__center',
            'created_by',
            'updated_by',
            'reviewed_by'
        )

        # Filter by student if provided (for student portal)
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(exam_date__exam_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(exam_date__exam_date__lte=end_date)

        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status == 'paid':
            queryset = queryset.filter(amount_paid__gt=0)
        elif payment_status == 'unpaid':
            queryset = queryset.filter(amount_paid=0)

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
    def confirm(self, request, pk=None):
        """
        Confirm a pending booking.
        """
        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {'error': 'Only pending bookings can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if exam date still has available slots
        if booking.exam_date.available_slots <= 0:
            return Response(
                {'error': 'No available slots for this exam date.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'confirmed'
        booking.updated_by = request.user
        booking.save()

        return Response({'status': 'booking confirmed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.
        """
        booking = self.get_object()
        if booking.status in ['completed', 'no_show']:
            return Response(
                {'error': 'Completed or no-show bookings cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'cancelled'
        booking.updated_by = request.user
        booking.save()

        return Response({'status': 'booking cancelled'})

    @action(detail=True, methods=['post'])
    def mark_attended(self, request, pk=None):
        """
        Mark a booking as attended (for exam day tracking).
        """
        booking = self.get_object()
        if booking.status != 'confirmed':
            return Response(
                {'error': 'Only confirmed bookings can be marked as attended.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.exam_attended = True
        booking.status = 'completed'
        booking.updated_by = request.user
        booking.save()

        return Response({'status': 'booking marked as attended'})

    @action(detail=True, methods=['post'])
    def mark_no_show(self, request, pk=None):
        """
        Mark a booking as no-show.
        """
        booking = self.get_object()
        if booking.status != 'confirmed':
            return Response(
                {'error': 'Only confirmed bookings can be marked as no-show.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'no_show'
        booking.updated_by = request.user
        booking.save()

        return Response({'status': 'booking marked as no-show'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get booking statistics.
        """
        queryset = self.get_queryset()

        # Total bookings
        total_bookings = queryset.count()

        # Bookings by status
        status_counts = queryset.values('status').annotate(count=Sum('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Revenue (amount paid)
        total_revenue = queryset.aggregate(total=Sum('amount_paid'))['total'] or 0

        # Upcoming exams
        upcoming_exams = queryset.filter(
            exam_date__exam_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).count()

        # Today's exams
        today = timezone.now().date()
        todays_exams = queryset.filter(
            exam_date__exam_date=today,
            status__in=['confirmed', 'completed', 'no_show']
        ).count()

        data = {
            'total_bookings': total_bookings,
            'status_breakdown': status_dict,
            'total_revenue': float(total_revenue),
            'upcoming_exams': upcoming_exams,
            'todays_exams': todays_exams
        }

        return Response(data)