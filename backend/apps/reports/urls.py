from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reports'

router = DefaultRouter()
router.register(r'categories', views.ReportCategoryViewSet)
router.register(r'templates', views.ReportTemplateViewSet)
router.register(r'generated', views.GeneratedReportViewSet)
router.register(r'schedules', views.ReportScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]