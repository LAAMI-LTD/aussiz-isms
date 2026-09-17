from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

router = DefaultRouter()
# Router will be populated when viewsets are created

urlpatterns = [
    path('', include(router.urls)),
    # Attendance endpoints will be added here
]