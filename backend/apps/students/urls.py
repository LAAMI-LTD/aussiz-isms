from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'students'

router = DefaultRouter()
router.register(r'', views.StudentViewSet, basename='student')
router.register(r'next-of-kin', views.NextOfKinViewSet, basename='next-of-kin')
router.register(r'documents', views.StudentDocumentViewSet, basename='student-document')

urlpatterns = [
    path('', include(router.urls)),
    # Registration endpoint is handled by the ViewSet's register action
    # Additional specific endpoints can be added here
]