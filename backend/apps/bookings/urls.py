from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'bookings'

router = DefaultRouter()
router.register(r'centers', views.IELTSExamCenterViewSet)
router.register(r'dates', views.IELTSExamDateViewSet)
router.register(r'bookings', views.IELTSExamBookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]