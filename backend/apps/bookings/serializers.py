from rest_framework import serializers
from .models import IELTSExamCenter, IELTSExamDate, IELTSExamBooking
from apps.students.models import Student
from apps.accounts.models import User
from apps.ielts.models import IELTSTest


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


class IELTSExamCenterSerializer(serializers.ModelSerializer):
    """Serializer for IELTSExamCenter model."""
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSExamCenter
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class IELTSExamDateSerializer(serializers.ModelSerializer):
    """Serializer for IELTSExamDate model."""
    center = IELTSExamCenterSerializer(read_only=True)
    center_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSExamDate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'filled_slots', 'available_slots']

    def validate(self, attrs):
        """Validate exam date data."""
        center_id = attrs.get('center_id')
        exam_date = attrs.get('exam_date')
        registration_deadline = attrs.get('registration_deadline')
        total_slots = attrs.get('total_slots')
        filled_slots = attrs.get('filled_slots', 0)

        # Check if registration deadline is not after exam date
        if registration_deadline and exam_date and registration_deadline > exam_date:
            raise serializers.ValidationError({
                'registration_deadline': 'Registration deadline cannot be after the exam date.'
            })

        # Check if filled slots don't exceed total slots
        if filled_slots is not None and total_slots is not None and filled_slots > total_slots:
            raise serializers.ValidationError({
                'filled_slots': 'Filled slots cannot exceed total slots.'
            })

        # Check if center exists
        if center_id:
            try:
                IELTSExamCenter.objects.get(id=center_id)
            except IELTSExamCenter.DoesNotExist:
                raise serializers.ValidationError({
                    'center_id': 'Invalid exam center.'
                })

        return attrs


class IELTSExamBookingSerializer(serializers.ModelSerializer):
    """Serializer for IELTSExamBooking model."""
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    exam_date = IELTSExamDateSerializer(read_only=True)
    exam_date_id = serializers.UUIDField(write_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = IELTSExamBooking
        fields = '__all__'
        read_only_fields = ['id', 'booking_date', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate(self, attrs):
        """Validate exam booking data."""
        student_id = attrs.get('student_id')
        exam_date_id = attrs.get('exam_date_id')
        status = attrs.get('status')
        amount_paid = attrs.get('amount_paid', 0)

        # Check if student exists
        if student_id:
            try:
                Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                raise serializers.ValidationError({
                    'student_id': 'Invalid student.'
                })

        # Check if exam date exists
        if exam_date_id:
            try:
                exam_date = IELTSExamDate.objects.get(id=exam_date_id)

                # Check if exam date is still available for booking (unless cancelling or completing)
                if status not in ['cancelled', 'completed'] and exam_date.available_slots <= 0:
                    raise serializers.ValidationError({
                        'exam_date_id': 'No available slots for this exam date.'
                    })

                # Check if registration deadline has passed
                from django.utils import timezone
                if status == 'pending' and timezone.now().date() > exam_date.registration_deadline:
                    raise serializers.ValidationError({
                        'exam_date_id': 'Registration deadline has passed for this exam date.'
                    })

                # Validate amount paid doesn't exceed exam fee
                if amount_paid > exam_date.exam_fee:
                    raise serializers.ValidationError({
                        'amount_paid': f'Amount paid cannot exceed exam fee ({exam_date.exam_fee}).'
                    })

            except IELTSExamDate.DoesNotExist:
                raise serializers.ValidationError({
                    'exam_date_id': 'Invalid exam date.'
                })

        # Check for duplicate booking (student already booked this exam date)
        if student_id and exam_date_id and status not in ['cancelled']:
            existing_booking = IELTSExamBooking.objects.filter(
                student_id=student_id,
                exam_date_id=exam_date_id,
                status__in=['pending', 'confirmed']  # Don't count cancelled/completed as active bookings
            ).exclude(
                id=getattr(self.instance, 'id', None)
            ).first()

            if existing_booking:
                raise serializers.ValidationError({
                    'non_field_errors': 'Student already has an active booking for this exam date.'
                })

        return attrs