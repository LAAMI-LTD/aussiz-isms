from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Student, NextOfKin, StudentDocument
from .serializers import StudentSerializer, NextOfKinSerializer, StudentDocumentSerializer
from apps.accounts.models import User


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students.
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'gender', 'nationality']
    search_fields = ['student_id', 'first_name', 'last_name', 'national_id_passport', 'email']
    ordering_fields = ['date_created', 'student_id', 'last_name']
    ordering = ['-date_created']

    def get_queryset(self):
        """
        Optionally restricts the returned students based on query parameters.
        """
        queryset = Student.objects.select_related('created_by', 'updated_by').prefetch_related('next_of_kin', 'documents')

        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by course enrollment if provided
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(enrollments__course_id=course_id, enrollments__is_active=True)

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
    def activate(self, request, pk=None):
        """
        Activate a student.
        """
        student = self.get_object()
        student.status = 'active'
        student.updated_by = request.user
        student.save()
        return Response({'status': 'student activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a student.
        """
        student = self.get_object()
        student.status = 'inactive'
        student.updated_by = request.user
        student.save()
        return Response({'status': 'student deactivated'})


class NextOfKinViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing next of kin records.
    """
    queryset = NextOfKin.objects.all()
    serializer_class = NextOfKinSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'phone_number']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class StudentDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student documents.
    """
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document_type', 'is_verified', 'student']
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']

    def perform_create(self, serializer):
        """
        Set the uploaded_by field to the current user.
        """
        serializer.save(uploaded_by=self.request.user)