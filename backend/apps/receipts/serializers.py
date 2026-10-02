from rest_framework import serializers
from .models import Receipt, ReceiptItem, ReceiptHistory
from apps.students.models import Student
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.finance.models import Payment, Invoice


class ReceiptItemSerializer(serializers.ModelSerializer):
    """
    Serializer for ReceiptItem model.
    """
    class Meta:
        model = ReceiptItem
        fields = [
            'id', 'description', 'quantity', 'unit_price',
            'line_total', 'is_taxable', 'tax_rate', 'tax_amount'
        ]
        read_only_fields = ['id', 'line_total', 'tax_amount']


class ReceiptHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for ReceiptHistory model.
    """
    changed_by = UserSerializer(read_only=True)

    class Meta:
        model = ReceiptHistory
        fields = [
            'id', 'changed_at', 'changed_by', 'change_description',
            'receipt_number_snapshot', 'amount_snapshot', 'issue_date_snapshot',
            'is_cancelled_snapshot', 'change_reason'
        ]
        read_only_fields = ['id']


class ReceiptSerializer(serializers.ModelSerializer):
    """
    Serializer for Receipt model.
    """
    items = ReceiptItemSerializer(many=True, read_only=True)
    history = ReceiptHistorySerializer(many=True, read_only=True)
    payment_details = serializers.SerializerMethodField()
    invoice_details = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Receipt
        fields = [
            'id', 'receipt_number', 'payment', 'invoice',
            'issue_date', 'amount', 'notes', 'terms_and_conditions',
            'pdf_file', 'pdf_generated_at', 'is_active', 'is_cancelled',
            'cancelled_at', 'cancelled_by', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'items', 'history',
            'payment_details', 'invoice_details', 'is_pdf_available'
        ]
        read_only_fields = [
            'id', 'receipt_number', 'issue_date', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'items', 'history', 'pdf_generated_at',
            'payment_details', 'invoice_details', 'is_pdf_available'
        ]

    def get_payment_details(self, obj):
        """Get details about the related payment."""
        if obj.payment:
            return {
                'id': str(obj.payment.id),
                'payment_number': obj.payment.payment_number,
                'amount': obj.payment.amount,
                'payment_method': obj.payment.payment_method,
                'status': obj.payment.status,
                'student': obj.payment.student.get_full_name() if obj.payment.student else None
            }
        return None

    def get_invoice_details(self, obj):
        """Get details about the related invoice."""
        if obj.invoice:
            return {
                'id': str(obj.invoice.id),
                'invoice_number': obj.invoice.invoice_number,
                'issue_date': obj.invoice.issue_date,
                'due_date': obj.invoice.due_date,
                'status': obj.invoice.status,
                'student': obj.invoice.student.get_full_name() if obj.invoice.student else None
            }
        return None

    def validate(self, attrs):
        """Validate receipt data."""
        # Ensure amount matches payment if payment is provided
        payment = attrs.get('payment')
        amount = attrs.get('amount')

        if payment and amount is not None:
            if amount != payment.amount:
                raise serializers.ValidationError({
                    'amount': 'Receipt amount must match payment amount.'
                })

        return attrs

    def create(self, validated_data):
        """Create and return a new receipt."""
        # Create the receipt
        receipt = Receipt.objects.create(**validated_data)

        # Create history entry
        ReceiptHistory.objects.create(
            receipt=receipt,
            changed_by=validated_data.get('created_by'),
            change_description='Receipt created',
            change_reason='Initial creation'
        )

        return receipt

    def update(self, instance, validated_data):
        """Update and return an existing receipt."""
        # Track what changed for history
        changes = []
        for field, value in validated_data.items():
            if hasattr(instance, field) and getattr(instance, field) != value:
                changes.append(field)

        # Update the receipt
        receipt = super().update(instance, validated_data)

        # Create history entry if there were changes
        if changes:
            ReceiptHistory.objects.create(
                receipt=receipt,
                changed_by=validated_data.get('updated_by'),
                change_description=f'Updated fields: {", ".join(changes)}',
                change_reason='User update'
            )

        return receipt


class ReceiptGenerateSerializer(serializers.Serializer):
    """
    Serializer for generating a receipt from a payment.
    """
    payment_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)
    terms_and_conditions = serializers.CharField(required=False, allow_blank=True)

    def validate_payment_id(self, value):
        """Validate that the payment exists and doesn't already have a receipt."""
        try:
            payment = Payment.objects.get(id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment does not exist.")

        # Check if payment already has a receipt
        if hasattr(payment, 'receipt'):
            raise serializers.ValidationError("Payment already has a receipt.")

        return value