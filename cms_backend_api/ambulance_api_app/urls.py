# ambulance_api_app/urls.py
from django.urls import path
from .views import (
    AmbulanceCreateView, AmbulanceListView, AmbulanceUpdateView,
    AmbulanceRequestCreateView, AmbulanceRequestListView, update_request_status
)

urlpatterns = [
    path('ambulances/', AmbulanceListView.as_view(), name='ambulance-list'),
    path('ambulances/create/', AmbulanceCreateView.as_view(), name='ambulance-create'),
    path('ambulances/update/<int:pk>/', AmbulanceUpdateView.as_view(), name='ambulance-update'),

    path('requests/', AmbulanceRequestListView.as_view(), name='ambulance-request-list'),
    path('requests/create/', AmbulanceRequestCreateView.as_view(), name='ambulance-request-create'),
    path('requests/<int:request_id>/update-status/', update_request_status, name='update-request-status'),
]
