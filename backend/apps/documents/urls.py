from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'documents'

router = DefaultRouter()
router.register(r'document-types', views.DocumentTypeViewSet)
router.register(r'document-categories', views.DocumentCategoryViewSet)
router.register(r'document-templates', views.DocumentTemplateViewSet)
router.register(r'bulk-operations', views.BulkDocumentOperationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]