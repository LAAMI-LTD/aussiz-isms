from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'classes'

router = DefaultRouter()
router.register(r'', views.ClassViewSet, basename='class')

urlpatterns = [
    path('', include(router.urls)),
]