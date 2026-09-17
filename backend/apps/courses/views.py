from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import CourseCategory, Course, Class
from .serializers import CourseCategorySerializer, CourseSerializer, ClassSerializer
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
        Set the created_by field to the current user.
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Set the updated_by field to the current user.
        """
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