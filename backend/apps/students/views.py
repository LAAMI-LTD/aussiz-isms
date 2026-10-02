from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Student, NextOfKin, StudentDocument
from .serializers import StudentSerializer, NextOfKinSerializer, StudentDocumentSerializer, StudentRegistrationSerializer
from apps.accounts.models import User
from apps.accounts.permissions import IsHODOrAbove, IsStudentOwnerOrStaff
import logging

logger = logging.getLogger(__name__)


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

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            # Anyone authenticated can view student list or detail
            permission_classes = [IsAuthenticated]
        elif self.action == 'register':
            # Only HOD and Super Admin can register students
            permission_classes = [IsHODOrAbove]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only HOD and Super Admin can create/update/delete students
            # (Note: create is handled by our custom register action)
            permission_classes = [IsHODOrAbove]
        elif self.action in ['activate', 'deactivate']:
            # Only HOD and Super Admin can activate/deactivate students
            permission_classes = [IsHODOrAbove]
        else:
            # Default to authenticated users for any other actions
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally restricts the returned students based on query parameters.
        """
        queryset = Student.objects.select_related('created_by', 'updated_by').prefetch_related('next_of_kin_entries', 'documents')

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

    def create(self, request, *args, **kwargs):
        """
        Disable default create endpoint - use /register/ instead.
        """
        return Response(
            {
                'error': 'Direct student creation is not allowed. Use the /register/ endpoint instead.'
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new student with automatic student ID generation.
        Expected to be used by staff (HOD or Super Admin) for new admissions.
        """
        serializer = StudentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save(created_by=request.user, updated_by=request.user)

        logger.info(f"New student registered: {student.student_id} - {student.get_full_name()} by {request.user.username}")

        return Response(
            StudentSerializer(student).data,
            status=status.HTTP_201_CREATED
        )


class NextOfKinViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing next of kin records.
    """
    serializer_class = NextOfKinSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'phone_number']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned next of kin records based on student_pk from URL.
        """
        queryset = NextOfKin.objects.all()

        # If accessing via nested route under a student, filter by that student
        student_pk = self.kwargs.get('student_pk')
        if student_pk:
            queryset = queryset.filter(student_id=student_pk)

        return queryset

    def perform_create(self, serializer):
        """
        When creating a next of kin record via nested route, associate it with the parent student.
        """
        student_pk = self.kwargs.get('student_pk')
        if student_pk:
            serializer.save(student_id=student_pk)
        else:
            serializer.save()


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

    def get_queryset(self):
        """
        Optionally restricts the returned documents based on student_pk from URL.
        """
        queryset = StudentDocument.objects.all()

        # If accessing via nested route under a student, filter by that student
        student_pk = self.kwargs.get('student_pk')
        if student_pk:
            queryset = queryset.filter(student_id=student_pk)

        return queryset

    def perform_create(self, serializer):
        """
        When creating a document record via nested route, associate it with the parent student.
        """
        student_pk = self.kwargs.get('student_pk')
        if student_pk:
            serializer.save(student_id=student_pk)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """
        Set the uploaded_by field to the current user.
        """
        serializer.save(uploaded_by=self.request.user)