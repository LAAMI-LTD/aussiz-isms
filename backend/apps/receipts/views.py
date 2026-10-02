from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from .models import Receipt, ReceiptItem, ReceiptHistory
from .serializers import (
    ReceiptSerializer, ReceiptItemSerializer, ReceiptHistorySerializer,
    ReceiptGenerateSerializer
)
from apps.finance.models import Payment
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)


class ReceiptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing receipts.
    """
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_cancelled', 'issue_date']
    search_fields = ['receipt_number', 'notes']
    ordering_fields = ['issue_date', 'receipt_number', 'amount']
    ordering = ['-issue_date']

    def get_queryset(self):
        """
        Optionally restricts the returned receipts based on query parameters.
        """
        queryset = Receipt.objects.select_related(
            'payment', 'invoice', 'created_by', 'updated_by', 'cancelled_by'
        ).prefetch_related('items', 'history')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(issue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__lte=end_date)

        # Filter by amount range if provided
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

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

    @action(detail=False, methods=['post'])
    def generate_from_payment(self, request):
        """
        Generate a receipt from a payment.
        """
        serializer = ReceiptGenerateSerializer(data=request.data)
        if serializer.is_valid():
            payment_id = serializer.validated_data['payment_id']
            notes = serializer.validated_data.get('notes', '')
            terms_and_conditions = serializer.validated_data.get('terms_and_conditions', '')

            try:
                payment = get_object_or_404(Payment, id=payment_id)

                # Check if payment already has a receipt
                if hasattr(payment, 'receipt'):
                    return Response(
                        {'error': 'Payment already has a receipt'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Create the receipt
                receipt = Receipt.objects.create(
                    payment=payment,
                    invoice=getattr(payment, 'invoice', None),
                    notes=notes,
                    terms_and_conditions=terms_and_conditions,
                    created_by=request.user
                )

                # Create history entry
                ReceiptHistory.objects.create(
                    receipt=receipt,
                    changed_by=request.user,
                    change_description='Receipt generated from payment',
                    change_reason='Payment reconciliation'
                )

                # Serialize and return the receipt
                receipt_serializer = ReceiptSerializer(receipt, context={'request': request})
                return Response({
                    'message': 'Receipt generated successfully',
                    'receipt': receipt_serializer.data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Error generating receipt from payment {payment_id}: {str(e)}")
                return Response(
                    {'error': 'Failed to generate receipt'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """
        Generate PDF for a receipt.
        """
        receipt = self.get_object()
        try:
            # In a real implementation, this would generate and save a PDF
            # For now, we'll just update the timestamp
            receipt.pdf_generated_at = timezone.now()
            receipt.save(update_fields=['pdf_generated_at'])

            # Create history entry
            ReceiptHistory.objects.create(
                receipt=receipt,
                changed_by=request.user,
                change_description='PDF generated for receipt',
                change_reason='User requested PDF generation'
            )

            return Response({
                'message': 'PDF generated successfully',
                'pdf_generated_at': receipt.pdf_generated_at
            })
        except Exception as e:
            logger.error(f"Error generating PDF for receipt {receipt.id}: {str(e)}")
            return Response(
                {'error': 'Failed to generate PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a receipt.
        """
        receipt = self.get_object()
        if receipt.is_cancelled:
            return Response(
                {'error': 'Receipt is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            receipt.cancel(cancelled_by_user=request.user)

            # Create history entry
            ReceiptHistory.objects.create(
                receipt=receipt,
                changed_by=request.user,
                change_description='Receipt cancelled',
                change_reason='User requested cancellation'
            )

            return Response({
                'message': 'Receipt cancelled successfully',
                'is_cancelled': receipt.is_cancelled,
                'cancelled_at': receipt.cancelled_at
            })
        except Exception as e:
            logger.error(f"Error cancelling receipt {receipt.id}: {str(e)}")
            return Response(
                {'error': 'Failed to cancel receipt'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get history entries for a receipt.
        """
        receipt = self.get_object()
        history = receipt.history_entries.all()
        serializer = ReceiptHistorySerializer(history, many=True)
        return Response(serializer.data)


class ReceiptItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing receipt items (read-only).
    """
    queryset = ReceiptItem.objects.all()
    serializer_class = ReceiptItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['receipt', 'is_taxable']
    search_fields = ['description']
    ordering_fields = ['unit_price', 'line_total']
    ordering = ['id']

    def get_queryset(self):
        """
        Optionally restricts the returned receipt items based on query parameters.
        """
        queryset = ReceiptItem.objects.select_related('receipt')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(receipt__issue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(receipt__issue_date__lte=end_date)

        return queryset


class ReceiptHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing receipt history (read-only).
    """
    queryset = ReceiptHistory.objects.all()
    serializer_class = ReceiptHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['receipt', 'changed_at']
    search_fields = ['change_description', 'change_reason']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']

    def get_queryset(self):
        """
        Optionally restricts the returned receipt history based on query parameters.
        """
        queryset = ReceiptHistory.objects.select_related('receipt', 'changed_by')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(changed_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(changed_at__lte=end_date)

        return queryset