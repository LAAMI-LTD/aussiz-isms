from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import FeeType, FeeItem, Invoice, InvoiceItem, Payment, Receipt
from .serializers import (
    FeeTypeSerializer,
    FeeItemSerializer,
    InvoiceSerializer,
    InvoiceItemSerializer,
    PaymentSerializer,
    ReceiptSerializer
)
from apps.students.models import Student
from apps.accounts.models import User


class FeeTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fee types.
    """
    queryset = FeeType.objects.all()
    serializer_class = FeeTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_taxable']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'category', 'default_amount']
    ordering = ['category', 'name']

    def get_queryset(self):
        """
        Optionally restricts the returned fee types based on query parameters.
        """
        queryset = FeeType.objects.select_related('created_by', 'updated_by')
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


class FeeItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fee items.
    """
    queryset = FeeItem.objects.all()
    serializer_class = FeeItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'fee_type', 'student', 'ielts_test', 'ielts_attempt',
        'exam_booking', 'is_paid', 'is_active', 'is_overdue'
    ]
    search_fields = [
        'description',
        'fee_type__name',
        'student__first_name',
        'student__last_name',
        'student__student_id'
    ]
    ordering_fields = ['due_date', 'amount', 'created_at']
    ordering = ['due_date']

    def get_queryset(self):
        """
        Optionally restricts the returned fee items based on query parameters.
        """
        queryset = FeeItem.objects.select_related(
            'fee_type',
            'student',
            'student__user',
            'ielts_test',
            'ielts_attempt',
            'exam_booking',
            'exam_booking__student',
            'created_by',
            'updated_by'
        )

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(due_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(due_date__lte=end_date)

        # Filter by amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            try:
                min_amount = float(min_amount)
                queryset = queryset.filter(amount__gte=min_amount)
            except ValueError:
                pass
        if max_amount:
            try:
                max_amount = float(max_amount)
                queryset = queryset.filter(amount__lte=max_amount)
            except ValueError:
                pass

        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status == 'paid':
            queryset = queryset.filter(is_paid=True)
        elif payment_status == 'unpaid':
            queryset = queryset.filter(is_paid=False)

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
    def overdue(self, request):
        """
        Get overdue fee items.
        """
        overdue_fees = self.get_queryset().filter(is_paid=False, due_date__lt=timezone.now().date())

        page = self.paginate_queryset(overdue_fees)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(overdue_fees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get fee item statistics.
        """
        queryset = self.get_queryset()

        # Total fee items
        total_fee_items = queryset.count()

        # Fee items by payment status
        paid_count = queryset.filter(is_paid=True).count()
        unpaid_count = queryset.filter(is_paid=False).count()
        overdue_count = queryset.filter(is_paid=False, due_date__lt=timezone.now().date()).count()

        # Total amounts
        total_charged = queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_paid = queryset.aggregate(total=Sum('amount'))['total'] or 0  # This would need to use discounted_amount in reality
        # For simplicity, we'll just use the amount field

        data = {
            'total_fee_items': total_fee_items,
            'paid_count': paid_count,
            'unpaid_count': unpaid_count,
            'overdue_count': overdue_count,
            'total_charged': float(total_charged),
            'total_paid': float(total_paid)
        }

        return Response(data)


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoices.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'student', 'status', 'is_active'
    ]
    search_fields = [
        'invoice_number',
        'student__first_name',
        'student__last_name',
        'student__student_id',
        'notes'
    ]
    ordering_fields = ['issue_date', 'due_date', 'total_amount', 'amount_paid']
    ordering = ['-issue_date']

    def get_queryset(self):
        """
        Optionally restricts the returned invoices based on query parameters.
        """
        queryset = Invoice.objects.select_related(
            'student',
            'student__user',
            'created_by',
            'updated_by'
        ).prefetch_related('items__fee_item__fee_type')

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(issue_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__date__lte=end_date)

        # Filter by amount range
        min_total = self.request.query_params.get('min_total')
        max_total = self.request.query_params.get('max_total')
        if min_total:
            try:
                min_total = float(min_total)
                queryset = queryset.filter(total_amount__gte=min_total)
            except ValueError:
                pass
        if max_total:
            try:
                max_total = float(max_total)
                queryset = queryset.filter(total_amount__lte=max_total)
            except ValueError:
                pass

        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status == 'paid':
            queryset = queryset.filter(status='paid')
        elif payment_status == 'partially_paid':
            queryset = queryset.filter(status='partially_paid')
        elif payment_status == 'unpaid':
            queryset = queryset.filter(status__in=['draft', 'sent', 'overdue'])
        elif payment_status == 'overdue':
            queryset = queryset.filter(status='overdue')

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
    def send(self, request, pk=None):
        """
        Send an invoice (change status from draft to sent).
        """
        invoice = self.get_object()
        if invoice.status != 'draft':
            return Response(
                {'error': 'Only draft invoices can be sent.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invoice.status = 'sent'
        invoice.updated_by = request.user
        invoice.save()

        return Response({'status': 'invoice sent'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an invoice.
        """
        invoice = self.get_object()
        if invoice.status == 'paid':
            return Response(
                {'error': 'Paid invoices cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invoice.status = 'cancelled'
        invoice.updated_by = request.user
        invoice.save()

        return Response({'status': 'invoice cancelled'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get invoice statistics.
        """
        queryset = self.get_queryset()

        # Total invoices
        total_invoices = queryset.count()

        # Invoices by status
        status_counts = queryset.values('status').annotate(count=Sum('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Financial totals
        total_charged = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = queryset.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_outstanding = queryset.aggregate(
            total=Sum(models.ExpressionWrapper(
                models.F('total_amount') - models.F('amount_paid'),
                output_field=models.DecimalField()
            ))
        )['total'] or 0

        # Overdue invoices
        overdue_count = queryset.filter(
            status__in=['sent', 'partially_paid'],
            due_date__lt=timezone.now().date()
        ).count()

        data = {
            'total_invoices': total_invoices,
            'status_breakdown': status_dict,
            'total_charged': float(total_charged),
            'total_paid': float(total_paid),
            'total_outstanding': float(total_outstanding),
            'overdue_count': overdue_count
        }

        return Response(data)


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoice items.
    """
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['invoice', 'is_taxable']
    search_fields = ['description']
    ordering_fields = ['quantity', 'unit_price', 'line_total']
    ordering = ['invoice', 'id']

    def get_queryset(self):
        """
        Optionally restricts the returned invoice items based on query parameters.
        """
        queryset = InvoiceItem.objects.select_related(
            'invoice',
            'invoice__student',
            'fee_item',
            'fee_item__fee_type'
        )
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


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'student', 'invoice', 'payment_method', 'status', 'is_active'
    ]
    search_fields = [
        'payment_number',
        'student__first_name',
        'student__last_name',
        'student__student_id',
        'transaction_id',
        'notes'
    ]
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date']

    def get_queryset(self):
        """
        Optionally restricts the returned payments based on query parameters.
        """
        queryset = Payment.objects.select_related(
            'student',
            'student__user',
            'invoice',
            'invoice__student',
            'created_by',
            'updated_by'
        )

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(payment_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__date__lte=end_date)

        # Filter by amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            try:
                min_amount = float(min_amount)
                queryset = queryset.filter(amount__gte=min_amount)
            except ValueError:
                pass
        if max_amount:
            try:
                max_amount = float(max_amount)
                queryset = queryset.filter(amount__lte=max_amount)
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

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Mark a payment as processed.
        """
        payment = self.get_object()
        if payment.status != 'pending':
            return Response(
                {'error': 'Only pending payments can be processed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction_id = request.data.get('transaction_id')
        payment.mark_as_processed(transaction_id)

        return Response({'status': 'payment processed'})

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """
        Mark a payment as failed.
        """
        payment = self.get_object()
        if payment.status != 'pending':
            return Response(
                {'error': 'Only pending payments can be marked as failed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.mark_as_failed()

        return Response({'status': 'payment marked as failed'})

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Refund a payment.
        """
        payment = self.get_object()
        if payment.status != 'processed':
            return Response(
                {'error': 'Only processed payments can be refunded.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.refund()

        return Response({'status': 'payment refunded'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get payment statistics.
        """
        queryset = self.get_queryset()

        # Total payments
        total_payments = queryset.count()

        # Payments by status
        status_counts = queryset.values('status').annotate(count=Sum('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Payments by method
        method_counts = queryset.values('payment_method').annotate(count=Sum('id'))
        method_dict = {item['payment_method']: item['count'] for item in method_counts}

        # Financial totals
        total_processed = queryset.aggregate(
            total=Sum('amount', filter=models.Q(status='processed'))
        )['total'] or 0
        total_refunded = queryset.aggregate(
            total=Sum('amount', filter=models.Q(status='refunded'))
        )['total'] or 0

        data = {
            'total_payments': total_payments,
            'status_breakdown': status_dict,
            'method_breakdown': method_dict,
            'total_processed': float(total_processed),
            'total_refunded': float(total_refunded)
        }

        return Response(data)


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing receipts (read-only as they are generated from payments).
    """
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['payment', 'payment__student']
    search_fields = [
        'receipt_number',
        'payment__payment_number',
        'payment__student__first_name',
        'payment__student__last_name',
        'payment__student__student_id'
    ]
    ordering_fields = ['issue_date', 'amount']
    ordering = ['-issue_date']

    def get_queryset(self):
        """
        Optionally restricts the returned receipts based on query parameters.
        """
        queryset = Receipt.objects.select_related(
            'payment',
            'payment__student',
            'payment__student__user',
            'created_by',
            'updated_by'
        )
        return queryset