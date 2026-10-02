from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'students'

router = DefaultRouter()
router.register(r'', views.StudentViewSet, basename='student')

# Nested routes for next of kin and documents under students
# We'll manually define these since DRF DefaultRouter doesn't support nesting natively
urlpatterns = [
    path('', include(router.urls)),
    # Nested routes for next of kin
    path('<uuid:student_pk>/next-of-kin/', views.NextOfKinViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='student-next-of-kin-list'),
    path('<uuid:student_pk>/next-of-kin/<uuid:pk>/', views.NextOfKinViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='student-next-of-kin-detail'),
    # Nested routes for documents
    path('<uuid:student_pk>/documents/', views.StudentDocumentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='student-documents-list'),
    path('<uuid:student_pk>/documents/<uuid:pk>/', views.StudentDocumentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='student-documents-detail'),
]