from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

router = DefaultRouter()
router.register(r'sessions', views.AttendanceSessionViewSet)
router.register(r'statuses', views.AttendanceStatusViewSet)
router.register(r'records', views.AttendanceRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]