from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'ielts'

router = DefaultRouter()
router.register(r'tests', views.IELTSTestViewSet)
router.register(r'sections', views.IELTSTestSectionViewSet)
router.register(r'attempts', views.IELTSTestAttemptViewSet)
router.register(r'section-scores', views.IELTSTestSectionScoreViewSet)
router.register(r'progress', views.IELTSProgressViewSet)

urlpatterns = [
    path('', include(router.urls)),
]