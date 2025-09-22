from django.urls import path
from .views import PatientListCreateView, PatientRetrieveUpdateDisableView, SearchPatientView

urlpatterns = [
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<int:pk>/', PatientRetrieveUpdateDisableView.as_view(), name='patient-retrieve-update-disable'),
    path('patients/search/', SearchPatientView.as_view(), name='patient-search'),
]
