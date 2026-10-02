from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'receipts'

router = DefaultRouter()
router.register(r'receipts', views.ReceiptViewSet)
router.register(r'items', views.ReceiptItemViewSet)
router.register(r'history', views.ReceiptHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]