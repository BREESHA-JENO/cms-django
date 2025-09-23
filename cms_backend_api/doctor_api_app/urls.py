from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConsultationNotesViewSet,
    PrescriptionMedViewSet,
    PrescriptionLabViewSet,
)

# Router will auto-generate CRUD endpoints
router = DefaultRouter()
router.register(r"consultations", ConsultationNotesViewSet, basename="consultations")
router.register(r"prescriptions/med", PrescriptionMedViewSet, basename="prescriptions-med")
router.register(r"prescriptions/lab", PrescriptionLabViewSet, basename="prescriptions-lab")

urlpatterns = [
    path("", include(router.urls)),
]
