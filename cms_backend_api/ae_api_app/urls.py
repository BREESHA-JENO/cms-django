from django.urls import path
from .views import (
    TempPatientCreateView, TempPatientListView,
    AECaseCreateView, AECaseListView, assign_ambulance,
    EmergencyTreatmentCreateView, EmergencyTreatmentListView,
    convert_temp_to_patient
)

urlpatterns = [
    # Temp Patient
    path('temp-patient/create/', TempPatientCreateView.as_view(), name='temp_patient_create'),
    path('temp-patient/list/', TempPatientListView.as_view(), name='temp_patient_list'),

    # AECase
    path('ae-case/create/', AECaseCreateView.as_view(), name='ae_case_create'),
    path('ae-case/list/', AECaseListView.as_view(), name='ae_case_list'),
    path('ae-case/<int:ae_case_id>/assign-ambulance/', assign_ambulance, name='assign_ambulance'),

    # Emergency Treatment
    path('treatment/create/', EmergencyTreatmentCreateView.as_view(), name='treatment_create'),
    path('treatment/list/', EmergencyTreatmentListView.as_view(), name='treatment_list'),

    # Convert TempPatient -> Permanent
    path('temp-patient/<int:temp_patient_id>/convert/', convert_temp_to_patient, name='convert_temp_to_patient'),
]
