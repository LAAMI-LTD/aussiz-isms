from rest_framework import serializers
from .models import FeeType, FeeItem, Invoice, InvoiceItem, Payment, Receipt
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest, IELTSTestAttempt
from apps.bookings.models import IELTSExamBooking


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model (nested)."""
    class Meta:
        model = Student
        fields = ['id', 'student_id', 'first_name', 'last_name']
        read_only_fields = fields


class IELTSTestSerializer(serializers.ModelSerializer):
    """Serializer for IELTSTest model (nested)."""
    class Meta:
        model = IELTSTest
        fields = ['id', 'title', 'test_type', 'test_mode']
        read_only_fields = fields


class IELTSTestAttemptSerializer(serializers.ModelSerializer):
    """Serializer for IELTSTestAttempt model (nested)."""
    class Meta:
        model = IELTSTestAttempt
        fields = ['id', 'status', 'overall_band_score']
        read_only_fields = fields


class IELTSExamBookingSerializer(serializers.ModelSerializer):
    """Serializer for IELTSExamBooking model (nested)."""
    class Meta:
        model = IELTSExamBooking
        fields = ['id', 'status']
        read_only_fields = fields


class FeeTypeSerializer(serializers.ModelSerializer):
    """Serializer for FeeType model."""
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = FeeType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class FeeItemSerializer(serializers.ModelSerializer):
    """Serializer for FeeItem model."""
    fee_type = FeeTypeSerializer(read_only=True)
    fee_type_id = serializers.UUIDField(write_only=True)
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True, required=False)
    ielts_test = IELTSTestSerializer(read_only=True)
    ielts_test_id = serializers.UUIDField(write_only=True, required=False)
    ielts_attempt = IELTSTestAttemptSerializer(read_only=True)
    ielts_attempt_id = serializers.UUIDField(write_only=True, required=False)
    exam_booking = IELTSExamBookingSerializer(read_only=True)
    exam_booking_id = serializers.UUIDField(write_only=True, required=False)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = FeeItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'is_paid']

    def validate(self, attrs):
        """Validate fee item data."""
        fee_type_id = attrs.get('fee_type_id')
        student_id = attrs.get('student_id')
        ielts_test_id = attrs.get('ielts_test_id')
        ielts_attempt_id = attrs.get('ielts_attempt_id')
        exam_booking_id = attrs.get('exam_booking_id')
        amount = attrs.get('amount')
        discount_percentage = attrs.get('discount_percentage', 0)
        due_date = attrs.get('due_date')

        # Check if fee type exists
        if fee_type_id:
            try:
                FeeType.objects.get(id=fee_type_id)
            except FeeType.DoesNotExist:
                raise serializers.ValidationError({
                    'fee_type_id': 'Invalid fee type.'
                })

        # Validate discount percentage
        if discount_percentage is not None and (discount_percentage < 0 or discount_percentage > 100):
            raise serializers.ValidationError({
                'discount_percentage': 'Discount percentage must be between 0 and 100.'
            })

        # Validate amount
        if amount is not None and amount < 0:
            raise serializers.ValidationError({
                'amount': 'Amount cannot be negative.'
            })

        # Validate due date
        if due_date is not None and due_date < timezone.now().date():
            raise serializers.ValidationError({
                'due_date': 'Due date cannot be in the past.'
            })

        return attrs


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model."""
    fee_item = FeeItemSerializer(read_only=True)
    fee_item_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = InvoiceItem
        fields = '__all__'
        read_only_fields = ['id', 'line_total', 'tax_amount']

    def validate(self, attrs):
        """Validate invoice item data."""
        fee_item_id = attrs.get('fee_item_id')
        description = attrs.get('description')
        quantity = attrs.get('quantity')
        unit_price = attrs.get('unit_price')
        is_taxable = attrs.get('is_taxable', False)
        tax_rate = attrs.get('tax_rate', 0)

        # Check if fee item exists (if provided)
        if fee_item_id:
            try:
                FeeItem.objects.get(id=fee_item_id)
            except FeeItem.DoesNotExist:
                raise serializers.ValidationError({
                    'fee_item_id': 'Invalid fee item.'
                })

        # Validate description
        if not description or len(description.strip()) == 0:
            raise serializers.ValidationError({
                'description': 'Description is required.'
            })

        # Validate quantity
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({
                'quantity': 'Quantity must be greater than zero.'
            })

        # Validate unit price
        if unit_price is not None and unit_price < 0:
            raise serializers.ValidationError({
                'unit_price': 'Unit price cannot be negative.'
            })

        # Validate tax rate
        if tax_rate is not None and (tax_rate < 0 or tax_rate > 1):
            raise serializers.ValidationError({
                'tax_rate': 'Tax rate must be between 0 and 1.'
            })

        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'amount_paid']

    def validate(self, attrs):
        """Validate invoice data."""
        student_id = attrs.get('student_id')
        issue_date = attrs.get('issue_date')
        due_date = attrs.get('due_date')
        status = attrs.get('status', 'draft')
        subtotal = attrs.get('subtotal', 0)
        tax_amount = attrs.get('tax_amount', 0)
        total_amount = attrs.get('total_amount', 0)
        amount_paid = attrs.get('amount_paid', 0)

        # Check if student exists
        if student_id:
            try:
                Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                raise serializers.ValidationError({
                    'student_id': 'Invalid student.'
                })

        # Validate dates
        if issue_date and due_date and due_date < issue_date:
            raise serializers.ValidationError({
                'due_date': 'Due date cannot be before issue date.'
            })

        # Validate amounts
        if subtotal is not None and subtotal < 0:
            raise serializers.ValidationError({
                'subtotal': 'Subtotal cannot be negative.'
            })

        if tax_amount is not None and tax_amount < 0:
            raise serializers.ValidationError({
                'tax_amount': 'Tax amount cannot be negative.'
            })

        if total_amount is not None and total_amount < 0:
            raise serializers.ValidationError({
                'total_amount': 'Total amount cannot be negative.'
            })

        if amount_paid is not None and amount_paid < 0:
            raise serializers.ValidationError({
                'amount_paid': 'Amount paid cannot be negative.'
            })

        # Validate that total amount matches subtotal + tax amount (if provided)
        if subtotal is not None and tax_amount is not None and total_amount is not None:
            expected_total = subtotal + tax_amount
            if abs(total_amount - expected_total) > 0.01:  # Allow for small rounding differences
                raise serializers.ValidationError({
                    'total_amount': f'Total amount should be {expected_total} (subtotal + tax).'
                })

        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    invoice = InvoiceSerializer(read_only=True)
    invoice_id = serializers.UUIDField(write_only=True, required=False)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'payment_number']

    def validate(self, attrs):
        """Validate payment data."""
        student_id = attrs.get('student_id')
        invoice_id = attrs.get('invoice_id')
        amount = attrs.get('amount')
        payment_method = attrs.get('payment_method')
        status = attrs.get('status', 'pending')

        # Check if student exists
        if student_id:
            try:
                Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                raise serializers.ValidationError({
                    'student_id': 'Invalid student.'
                })

        # Check if invoice exists (if provided)
        if invoice_id:
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                # Validate that payment amount doesn't exceed invoice balance due
                if amount and amount > invoice.balance_due:
                    raise serializers.ValidationError({
                        'amount': f'Payment amount cannot exceed invoice balance due (${invoice.balance_due}).'
                    })
            except Invoice.DoesNotExist:
                raise serializers.ValidationError({
                    'invoice_id': 'Invalid invoice.'
                })

        # Validate amount
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({
                'amount': 'Payment amount must be greater than zero.'
            })

        # Validate payment method
        valid_payment_methods = [choice[0] for choice in Payment.PAYMENT_METHOD_CHOICES]
        if payment_method and payment_method not in valid_payment_methods:
            raise serializers.ValidationError({
                'payment_method': f'Invalid payment method. Must be one of {valid_payment_methods}.'
            })

        return attrs


class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for Receipt model."""
    payment = PaymentSerializer(read_only=True)
    payment_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Receipt
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'receipt_number', 'amount']

    def validate(self, attrs):
        """Validate receipt data."""
        payment_id = attrs.get('payment_id')
        amount = attrs.get('amount')
        issue_date = attrs.get('issue_date')

        # Check if payment exists
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                # Validate that receipt amount matches payment amount
                if amount and amount != payment.amount:
                    raise serializers.ValidationError({
                        'amount': f'Receipt amount must match payment amount (${payment.amount}).'
                    })
            except Payment.DoesNotExist:
                raise serializers.ValidationError({
                    'payment_id': 'Invalid payment.'
                })

        # Validate amount
        if amount is not None and amount < 0:
            raise serializers.ValidationError({
                'amount': 'Amount cannot be negative.'
            })

        # Validate issue date
        if issue_date and issue_date > timezone.now():
            raise serializers.ValidationError({
                'issue_date': 'Issue date cannot be in the future.'
            })

        return attrs