from django.urls import path
from .views import (
    AmbulanceCreateView, AmbulanceListView, AmbulanceUpdateView,
    AmbulanceRequestCreateView, AmbulanceRequestListView, update_request_status
)

urlpatterns = [
    # Ambulance
    path('ambulance/create/', AmbulanceCreateView.as_view(), name='ambulance_create'),
    path('ambulance/list/', AmbulanceListView.as_view(), name='ambulance_list'),
    path('ambulance/<int:pk>/update/', AmbulanceUpdateView.as_view(), name='ambulance_update'),

    # Ambulance Requests
    path('request/create/', AmbulanceRequestCreateView.as_view(), name='ambulance_request_create'),
    path('request/list/', AmbulanceRequestListView.as_view(), name='ambulance_request_list'),
    path('request/<int:request_id>/update-status/', update_request_status, name='ambulance_request_update_status'),
]
