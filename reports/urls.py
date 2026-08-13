from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, DashboardStatsView

router = DefaultRouter()
router.register('reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', DashboardStatsView.as_view()),
]