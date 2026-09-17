from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import AttendanceSession, AttendanceStatus, AttendanceRecord
from .serializers import AttendanceSessionSerializer, AttendanceStatusSerializer, AttendanceRecordSerializer
from apps.accounts.models import User


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance sessions.
    """
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['class_instance', 'session_date', 'is_active']
    search_fields = ['class_instance__name', 'topic', 'description']
    ordering_fields = ['session_date', 'session_number', 'created_at']
    ordering = ['-session_date', 'session_number']

    def get_queryset(self):
        """
        Optionally restricts the returned sessions based on query parameters.
        """
        queryset = AttendanceSession.objects.select_related(
            'class_instance', 'class_instance__course', 'created_by', 'updated_by'
        ).prefetch_related('attendance_records__student', 'attendance_records__status')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session_date__lte=end_date)

        # Filter by student if provided
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(attendance_records__student_id=student_id)

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
    def bulk_attendance(self, request, pk=None):
        """
        Record attendance for multiple students at once.
        Expected format:
        {
            "attendance_records": [
                {"student_id": "uuid", "status_code": "P", "remarks": "On time"},
                ...
            ]
        }
        """
        session = self.get_object()
        attendance_data = request.data.get('attendance_records', [])

        if not attendance_data:
            return Response(
                {'error': 'No attendance records provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        errors = []

        for record_data in attendance_data:
            student_id = record_data.get('student_id')
            status_code = record_data.get('status_code')
            remarks = record_data.get('remarks', '')

            try:
                student = Student.objects.get(id=student_id)
                status_obj = AttendanceStatus.objects.get(code=status_code)

                # Use update_or_create to avoid duplicates
                attendance_record, created = AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={
                        'status': status_obj,
                        'remarks': remarks,
                        'recorded_by': request.user
                    }
                )

                results.append({
                    'student_id': str(student.id),
                    'student_name': student.get_full_name(),
                    'status': status_obj.name,
                    'created': created,
                    'recorded_at': attendance_record.recorded_at
                })
            except Student.DoesNotExist:
                errors.append({
                    'student_id': student_id,
                    'error': 'Student not found'
                })
            except AttendanceStatus.DoesNotExist:
                errors.append({
                    'student_id': student_id,
                    'error': f'Invalid status code: {status_code}'
                })
            except Exception as e:
                errors.append({
                    'student_id': student_id,
                    'error': str(e)
                })

        return Response({
            'success': len(results),
            'errors': len(errors),
            'results': results,
            'error_details': errors
        })


class AttendanceStatusViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance statuses.
    """
    queryset = AttendanceStatus.objects.all()
    serializer_class = AttendanceStatusSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_present']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'points']
    ordering = ['code']


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual attendance records.
    """
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['session', 'student', 'status']
    search_fields = ['student__first_name', 'student__last_name', 'remarks']
    ordering_fields = ['recorded_at', 'student__last_name']
    ordering = ['-recorded_at']

    def get_queryset(self):
        """
        Optionally restricts the returned records based on query parameters.
        """
        queryset = AttendanceRecord.objects.select_related(
            'student', 'session', 'session__class_instance', 'session__class_instance__course',
            'status', 'recorded_by'
        )

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(session__session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session__session_date__lte=end_date)

        # Filter by course if provided
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(session__class_instance__course_id=course_id)

        return queryset

    def perform_create(self, serializer):
        """
        Set the recorded_by field to the current user.
        """
        serializer.save(recorded_by=self.request.user)