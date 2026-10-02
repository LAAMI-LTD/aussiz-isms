from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

router = DefaultRouter()
router.register(r'notification-types', views.NotificationTypeViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'device-tokens', views.DeviceTokenViewSet)
router.register(r'notification-templates', views.NotificationTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]