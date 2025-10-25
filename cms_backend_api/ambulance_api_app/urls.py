from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    AmbulanceViewSet,
    AmbulanceRequestCreateView, AmbulanceRequestListView, update_request_status
)

router = DefaultRouter()
router.register(r'ambulances', AmbulanceViewSet, basename='ambulance')

urlpatterns = [
    path('requests/', AmbulanceRequestListView.as_view(), name='ambulance-request-list'),
    path('requests/create/', AmbulanceRequestCreateView.as_view(), name='ambulance-request-create'),
    path('requests/<int:request_id>/update-status/', update_request_status, name='update-request-status'),
]

urlpatterns += router.urls
