from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import DocumentType, DocumentCategory, DocumentTemplate, BulkDocumentOperation
from .serializers import (
    DocumentTypeSerializer, DocumentCategorySerializer,
    DocumentTemplateSerializer, BulkDocumentOperationSerializer
)
from apps.students.models import Student
from apps.accounts.models import User


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document types.
    """
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_required']
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']

    def get_queryset(self):
        """
        Optionally restricts the returned document types based on query parameters.
        """
        queryset = DocumentType.objects.select_related('created_by', 'updated_by')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

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


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document categories.
    """
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']

    def get_queryset(self):
        """
        Optionally restricts the returned document categories based on query parameters.
        """
        queryset = DocumentCategory.objects.select_related('created_by', 'updated_by')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

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


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document templates.
    """
    queryset = DocumentTemplate.objects.all()
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """
        Optionally restricts the returned document templates based on query parameters.
        """
        queryset = DocumentTemplate.objects.select_related('created_by', 'updated_by')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

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
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a document template.
        """
        template = self.get_object()
        template.is_active = not template.is_active
        template.updated_by = request.user
        template.save()

        return Response({
            'message': f'Template "{template.name}" is now {"active" if template.is_active else "inactive"}',
            'is_active': template.is_active
        })


class BulkDocumentOperationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bulk document operations.
    """
    queryset = BulkDocumentOperation.objects.all()
    serializer_class = BulkDocumentOperationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['operation_type', 'status', 'target_all_students']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned bulk document operations based on query parameters.
        """
        queryset = BulkDocumentOperation.objects.select_related(
            'created_by', 'updated_by'
        ).prefetch_related('document_types', 'target_course', 'target_class')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # Filter by date range for operation timing if provided
        op_start_date = self.request.query_params.get('op_start_date')
        op_end_date = self.request.query_params.get('op_end_date')
        if op_start_date:
            queryset = queryset.filter(started_at__gte=op_start_date)
        if op_end_date:
            queryset = queryset.filter(started_at__lte=op_end_date)

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
    def start_operation(self, request, pk=None):
        """
        Start a bulk document operation.
        """
        operation = self.get_object()

        if operation.status != 'pending':
            return Response(
                {'error': 'Operation can only be started when in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        operation.status = 'processing'
        operation.started_at = timezone.now()
        operation.updated_by = request.user
        operation.save()

        # In a real implementation, this would trigger an asynchronous task
        # For now, we'll just mark it as started

        return Response({
            'message': 'Bulk document operation started',
            'status': operation.status
        })

    @action(detail=True, methods=['post'])
    def complete_operation(self, request, pk=None):
        """
        Complete a bulk document operation.
        """
        operation = self.get_object()

        if operation.status != 'processing':
            return Response(
                {'error': 'Operation can only be completed when in processing status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        operation.status = 'completed'
        operation.completed_at = timezone.now()
        operation.updated_by = request.user
        operation.save()

        return Response({
            'message': 'Bulk document operation completed',
            'status': operation.status
        })

    @action(detail=True, methods=['post'])
    def fail_operation(self, request, pk=None):
        """
        Mark a bulk document operation as failed.
        """
        operation = self.get_object()

        if operation.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Operation can only be failed when pending or processing'},
                status=status.HTTP_400_BAD_REQUEST
            )

        operation.status = 'failed'
        operation.completed_at = timezone.now()
        operation.updated_by = request.user
        operation.save()

        return Response({
            'message': 'Bulk document operation marked as failed',
            'status': operation.status
        })

    @action(detail=True, methods=['post'])
    def cancel_operation(self, request, pk=None):
        """
        Cancel a bulk document operation.
        """
        operation = self.get_object()

        if operation.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Operation can only be cancelled when pending or processing'},
                status=status.HTTP_400_BAD_REQUEST
            )

        operation.status = 'cancelled'
        operation.completed_at = timezone.now()
        operation.updated_by = request.user
        operation.save()

        return Response({
            'message': 'Bulk document operation cancelled',
            'status': operation.status
        })