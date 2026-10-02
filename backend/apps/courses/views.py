from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import CourseCategory, Course, Class, Enrollment
from .serializers import CourseCategorySerializer, CourseSerializer, ClassSerializer, EnrollmentSerializer
from apps.accounts.models import User


class CourseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing course categories.
    """
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing courses.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'course_type', 'delivery_mode', 'status', 'is_active']
    search_fields = ['course_code', 'name', 'description']
    ordering_fields = ['name', 'course_code', 'fee', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """
        Optionally restricts the returned courses based on query parameters.
        """
        queryset = Course.objects.select_related('category', 'created_by', 'updated_by')

        # Filter by active status if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by course type if provided
        course_type = self.request.query_params.get('course_type')
        if course_type:
            queryset = queryset.filter(course_type=course_type)

        return queryset

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user and handle category_id.
        """
        category_id = self.request.data.get('category_id')
        if category_id:
            serializer.save(created_by=self.request.user, category_id=category_id)
        else:
            serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Set the updated_by field to the current user and handle category_id.
        """
        category_id = self.request.data.get('category_id')
        if category_id:
            serializer.save(updated_by=self.request.user, category_id=category_id)
        else:
            serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        """
        Get all classes for a specific course.
        """
        course = self.get_object()
        classes = course.classes.all()
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get only active courses.
        """
        active_courses = self.get_queryset().filter(is_active=True, status='active')
        serializer = self.get_serializer(active_courses, many=True)
        return Response(serializer.data)


class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing class instances.
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'status', 'is_active']
    search_fields = ['name', 'course__name', 'course__course_code']
    ordering_fields = ['start_date', 'end_date', 'name', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        """
        Optionally restricts the returned classes based on query parameters.
        """
        queryset = Class.objects.select_related('course', 'course__category', 'created_by', 'updated_by').prefetch_related('enrollments')

        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        # Filter by ongoing/upcoming/completed
        date_filter = self.request.query_params.get('date_filter')
        today = models.DateField().default
        if date_filter == 'ongoing':
            queryset = queryset.filter(status='ongoing')
        elif date_filter == 'upcoming':
            queryset = queryset.filter(start_date__gt=today, status='planned')
        elif date_filter == 'completed':
            queryset = queryset.filter(status='completed')

        return queryset

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user and handle course_id.
        """
        course_id = self.request.data.get('course_id')
        if course_id:
            serializer.save(created_by=self.request.user, course_id=course_id)
        else:
            serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Set the updated_by field to the current user and handle course_id.
        """
        course_id = self.request.data.get('course_id')
        if course_id:
            serializer.save(updated_by=self.request.user, course_id=course_id)
        else:
            serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a class.
        """
        class_obj = self.get_object()
        class_obj.status = 'ongoing'
        class_obj.is_active = True
        class_obj.updated_by = request.user
        class_obj.save()
        return Response({'status': 'class activated'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark a class as completed.
        """
        class_obj = self.get_object()
        class_obj.status = 'completed'
        class_obj.is_active = False
        class_obj.updated_by = request.user
        class_obj.save()
        return Response({'status': 'class completed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a class.
        """
        class_obj = self.get_object()
        class_obj.status = 'cancelled'
        class_obj.is_active = False
        class_obj.updated_by = request.user
        class_obj.save()
        return Response({'status': 'class cancelled'})


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student enrollments.
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'class_instance', 'status', 'payment_status', 'is_active']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id',
                     'class_instance__name', 'class_instance__course__name', 'class_instance__course__course_code']
    ordering_fields = ['enrollment_date', 'amount_paid']
    ordering = ['-enrollment_date']

    def get_queryset(self):
        """
        Optionally restricts the returned enrollments based on query parameters.
        """
        queryset = Enrollment.objects.select_related(
            'student', 'class_instance', 'class_instance__course',
            'created_by', 'updated_by'
        )

        # Filter by course if provided
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(class_instance__course_id=course_id)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(enrollment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(enrollment_date__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user and handle student_id and class_instance_id.
        """
        student_id = self.request.data.get('student_id')
        class_instance_id = self.request.data.get('class_instance_id')
        if student_id and class_instance_id:
            serializer.save(created_by=self.request.user, student_id=student_id, class_instance_id=class_instance_id)
        else:
            serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Set the updated_by field to the current user and handle student_id and class_instance_id.
        """
        student_id = self.request.data.get('student_id')
        class_instance_id = self.request.data.get('class_instance_id')
        if student_id and class_instance_id:
            serializer.save(updated_by=self.request.user, student_id=student_id, class_instance_id=class_instance_id)
        else:
            serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm a pending enrollment.
        """
        enrollment = self.get_object()
        if enrollment.status != 'pending':
            return Response(
                {'error': 'Only pending enrollments can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        enrollment.status = 'confirmed'
        enrollment.updated_by = request.user
        enrollment.save()
        return Response({'status': 'enrollment confirmed'})

    @action(detail=True, methods=['post'])
    def drop(self, request, pk=None):
        """
        Drop an enrollment.
        """
        enrollment = self.get_object()
        if enrollment.status in ['completed', 'dropped']:
            return Response(
                {'error': 'Cannot drop a completed or already dropped enrollment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        enrollment.status = 'dropped'
        enrollment.is_active = False
        enrollment.updated_by = request.user
        enrollment.save()
        return Response({'status': 'enrollment dropped'})

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """
        Record a payment for an enrollment.
        """
        enrollment = self.get_object()
        amount = request.data.get('amount', 0)
        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError
        except ValueError:
            return Response(
                {'error': 'Invalid payment amount.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment.amount_paid += amount
        if enrollment.amount_paid >= enrollment.class_instance.course.fee:
            enrollment.payment_status = 'paid'
        elif enrollment.amount_paid > 0:
            enrollment.payment_status = 'partial'
        else:
            enrollment.payment_status = 'unpaid'
        enrollment.updated_by = request.user
        enrollment.save()
        return Response({
            'status': 'payment recorded',
            'amount_paid': enrollment.amount_paid,
            'payment_status': enrollment.payment_status
        })