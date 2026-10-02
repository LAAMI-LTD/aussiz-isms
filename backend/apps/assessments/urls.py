from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'assessments'

router = DefaultRouter()
router.register(r'assessments', views.AssessmentViewSet, basename='assessment')
router.register(r'practice-tests', views.PracticeTestViewSet, basename='practice-test')
router.register(r'mock-tests', views.MockTestViewSet, basename='mock-test')
router.register(r'test-scores', views.TestScoreViewSet, basename='test-score')
router.register(r'attempts', views.AssessmentAttemptViewSet, basename='assessment-attempt')
router.register(r'component-scores', views.ComponentScoreViewSet, basename='component-score')
router.register(r'target-bands', views.TargetBandViewSet, basename='target-band')

urlpatterns = [
    path('', include(router.urls)),
]