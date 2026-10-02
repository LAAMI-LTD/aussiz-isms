from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'results'

router = DefaultRouter()
router.register(r'results', views.IELTSResultViewSet)
router.register(r'verifications', views.IELTSResultVerificationViewSet)
router.register(r'audit', views.IELTSResultAuditViewSet)

urlpatterns = [
    path('', include(router.urls)),
]