from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LabTestCategoryViewSet,
    LabTestViewSet,
    LabResultViewSet,
    LabBillingViewSet,
)

router = DefaultRouter()
router.register(r'categories', LabTestCategoryViewSet, basename='labtestcategory')
router.register(r'tests', LabTestViewSet, basename='labtest')
router.register(r'results', LabResultViewSet, basename='labresult')
router.register(r'billings', LabBillingViewSet, basename='labbilling')

urlpatterns = [
    path('', include(router.urls)),
]
