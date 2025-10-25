from django.urls import path
from .views import (
    # Temporary Patient Views
    TempPatientCreateView,
    TempPatientListView,
    TempPatientDetailView,
    TempPatientUpdateView,
    TempPatientDeleteView,
    convert_temp_to_permanent,
    
    # AE Case Views
    AECaseCreateView,
    AECaseListView,
    AECaseDetailView,
    AECaseUpdateView,
    assign_ambulance,
    ae_case_search,  # ADD THIS
    
    # Emergency Treatment Views
    EmergencyTreatmentCreateView,
    EmergencyTreatmentListView,
    EmergencyTreatmentDetailView,
)

urlpatterns = [
    # ========== TEMPORARY PATIENT ENDPOINTS ==========
    path('temp-patient/', TempPatientListView.as_view(), name='temp_patient_list'),  # CHANGED
    path('temp-patient/create/', TempPatientCreateView.as_view(), name='temp_patient_create'),
    path('temp-patient/<int:temp_patient_id>/', TempPatientDetailView.as_view(), name='temp_patient_detail'),
    path('temp-patient/<int:temp_patient_id>/update/', TempPatientUpdateView.as_view(), name='temp_patient_update'),
    path('temp-patient/<int:temp_patient_id>/delete/', TempPatientDeleteView.as_view(), name='temp_patient_delete'),
    path('temp-patient/<int:temp_patient_id>/convert/', convert_temp_to_permanent, name='convert_temp_to_permanent'),
    
    # ========== AE CASE ENDPOINTS (FIXED PATHS) ==========
    path('case/', AECaseListView.as_view(), name='ae_case_list'),  # CHANGED FROM ae-case/list/
    path('case/create/', AECaseCreateView.as_view(), name='ae_case_create'),  # CHANGED
    path('case/<int:ae_case_id>/', AECaseDetailView.as_view(), name='ae_case_detail'),  # CHANGED
    path('case/<int:ae_case_id>/update/', AECaseUpdateView.as_view(), name='ae_case_update'),  # CHANGED
    path('case/<int:ae_case_id>/assign-ambulance/', assign_ambulance, name='assign_ambulance'),  # CHANGED
    path('case/search/', ae_case_search, name='ae_case_search'),  # NEW - ADD THIS
    
    # ========== EMERGENCY TREATMENT ENDPOINTS ==========
    path('treatment/create/', EmergencyTreatmentCreateView.as_view(), name='treatment_create'),
    path('treatment/list/', EmergencyTreatmentListView.as_view(), name='treatment_list'),
    path('treatment/<int:treatment_id>/', EmergencyTreatmentDetailView.as_view(), name='treatment_detail'),
]
