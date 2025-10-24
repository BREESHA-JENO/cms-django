from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConsultationNotesViewSet,
    PrescriptionMedViewSet,
    PrescriptionLabViewSet,
    DoctorAppointmentViewSet,
    doctor_dashboard_stats,
    doctor_appointments,
)

# Router will auto-generate CRUD endpoints
router = DefaultRouter()
router.register(r"consultations", ConsultationNotesViewSet, basename="consultations")
router.register(r"prescriptions/med", PrescriptionMedViewSet, basename="prescriptions-med")
router.register(r"prescriptions/lab", PrescriptionLabViewSet, basename="prescriptions-lab")
router.register(r'appointments', DoctorAppointmentViewSet, basename='doctor-appointments')

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", doctor_dashboard_stats, name="dashboard-stats"),
    path("appointments/", doctor_appointments, name="doctor-appointments"),
]
