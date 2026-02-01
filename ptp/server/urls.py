from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZoneViewSet

router = DefaultRouter()
router.register(r'zones', ZoneViewSet, basename='zone')

urlpatterns = [
    path('', include(router.urls)),
]
