from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'courses'

router = DefaultRouter()
router.register(r'categories', views.CourseCategoryViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'classes', views.ClassViewSet)
router.register(r'enrollments', views.EnrollmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]