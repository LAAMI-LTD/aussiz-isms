from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'finance'

router = DefaultRouter()
router.register(r'fee-types', views.FeeTypeViewSet)
router.register(r'fee-items', views.FeeItemViewSet)
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'invoice-items', views.InvoiceItemViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'receipts', views.ReceiptViewSet)

urlpatterns = [
    path('', include(router.urls)),
]