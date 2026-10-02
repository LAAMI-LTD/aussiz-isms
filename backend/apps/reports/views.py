from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import ReportCategory, ReportTemplate, GeneratedReport, ReportSchedule
from .serializers import (
    ReportCategorySerializer, ReportTemplateSerializer,
    GeneratedReportSerializer, ReportScheduleSerializer
)
import logging

logger = logging.getLogger(__name__)


class ReportCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing report categories.
    """
    queryset = ReportCategory.objects.all()
    serializer_class = ReportCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing report templates.
    """
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'report_type', 'format', 'is_active', 'is_scheduled']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['category', 'name']

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)


class GeneratedReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing generated reports.
    """
    queryset = GeneratedReport.objects.all()
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template', 'status', 'format', 'generated_at']
    search_fields = ['name', 'description', 'report_number']
    ordering_fields = ['generated_at', 'report_number', 'name']
    ordering = ['-generated_at']

    def get_queryset(self):
        """
        Optionally restricts the returned reports based on query parameters.
        """
        queryset = GeneratedReport.objects.select_related(
            'template', 'generated_by', 'created_by', 'updated_by'
        )

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(generated_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(generated_at__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        Manually trigger report generation.
        """
        report = self.get_object()
        if report.status != 'generating':
            return Response(
                {'error': 'Report can only be generated when in generating status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Mark as generating
            report.mark_as_generating()

            # In a real implementation, this would trigger an asynchronous task
            # to generate the report based on the template and parameters
            # For now, we'll simulate completion

            # Simulate report generation (in reality, this would be asynchronous)
            # For demo purposes, we'll mark it as completed immediately
            report.mark_as_completed()

            # Create a simple text file for demonstration
            # In reality, this would be the actual report content
            report_content = f"""Report: {report.name}
Generated: {timezone.now()}
Template: {report.template.name}
Parameters: {report.parameters}

This is a simulated report generation.
In a real implementation, this would contain the actual report data.
"""

            # Save the content (in a real app, this would be a proper file)
            # For now, we'll just note that generation is complete
            logger.info(f"Report {report.id} generated successfully")

            serializer = self.get_serializer(report)
            return Response({
                'message': 'Report generated successfully',
                'report': serializer.data
            })

        except Exception as e:
            logger.error(f"Error generating report {report.id}: {str(e)}")
            report.mark_as_failed()
            return Response(
                {'error': 'Failed to generate report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel report generation.
        """
        report = self.get_object()
        if report.status not in ['generating', 'completed']:
            return Response(
                {'error': 'Report can only be cancelled when generating or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if report.status == 'generating':
                report.mark_as_failed()
                message = 'Report generation cancelled'
            else:
                message = 'Report marked as cancelled'

            return Response({
                'message': message,
                'status': report.status
            })
        except Exception as e:
            logger.error(f"Error cancelling report {report.id}: {str(e)}")
            return Response(
                {'error': 'Failed to cancel report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing report schedules.
    """
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template', 'frequency', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'next_generation_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set the updated_by field to the current user."""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_now(self, request, pk=None):
        """
        Generate report immediately based on schedule.
        """
        schedule = self.get_object()
        try:
            # Create a generated report based on this schedule
            generated_report = GeneratedReport.objects.create(
                template=schedule.template,
                name=f"{schedule.name} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                description=schedule.description or f"Generated from schedule: {schedule.name}",
                format=schedule.template.format,
                parameters=schedule.parameters,
                generated_by=request.user,
                created_by=request.user
            )

            # Mark as generating
            generated_report.mark_as_generating()

            # In a real implementation, this would trigger asynchronous generation
            # For now, we'll mark as completed
            generated_report.mark_as_completed()

            # Update schedule last generated time
            schedule.last_generated_at = timezone.now()
            schedule.save(update_fields=['last_generated_at'])

            serializer = GeneratedReportSerializer(generated_report, context={'request': request})
            return Response({
                'message': 'Report generated from schedule successfully',
                'report': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error generating report from schedule {schedule.id}: {str(e)}")
            return Response(
                {'error': 'Failed to generate report from schedule'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )