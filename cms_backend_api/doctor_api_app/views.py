from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from Authentication.permissions import IsDoctor
from .permissions import IsAssignedDoctor
from .serializers import DoctorAppointmentSerializer
from receptionist_api_app.models import Appointment
from .models import ConsultationNotes, PrescriptionMed, PrescriptionLab
from .serializers import (
    ConsultationNotesSerializer,
    PrescriptionMedSerializer,
    PrescriptionLabSerializer,
)


# -------------------------
# Common mixin for disabling updates & deletes
# -------------------------
class NoUpdateDeleteMixin:
    """Mixin to block update and delete operations."""

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Updates are not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Partial updates are not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Deletions are not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# -------------------------
# Mixin to filter queryset by logged-in staff
# -------------------------
class StaffFilteredQuerysetMixin:
    """Filters queryset to only objects belonging to the logged-in staff (unless superuser)."""

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if hasattr(user, "staff_profile") and not user.is_superuser:
            return qs.filter(staff_id=user.staff_profile)
        return qs


# -------------------------
# ConsultationNotes ViewSet
# -------------------------
class ConsultationNotesViewSet(NoUpdateDeleteMixin, StaffFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = ConsultationNotes.objects.all()
    serializer_class = ConsultationNotesSerializer
    permission_classes = [IsAuthenticated, IsDoctor, IsAssignedDoctor]

    def perform_create(self, serializer):
        """Auto-assign the logged-in doctor and ensure they are assigned to this appointment."""
        staff = self.request.user.staff_profile
        appointment = serializer.validated_data.get("appointment_id")

        # ✅ Check that this doctor is assigned to this appointment
        if appointment.staff != staff:
            raise PermissionDenied("You are not assigned to this patient's appointment.")

        serializer.save(staff_id=staff)


# -------------------------
# PrescriptionMed ViewSet
# -------------------------
class PrescriptionMedViewSet(NoUpdateDeleteMixin, StaffFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = PrescriptionMed.objects.all()
    serializer_class = PrescriptionMedSerializer
    permission_classes = [IsAuthenticated, IsDoctor, IsAssignedDoctor]

    def perform_create(self, serializer):
        """Auto-assign staff_id from request user"""
        staff = self.request.user.staff_profile
        consultation = serializer.validated_data.get("consultation_id")
        appointment = consultation.appointment_id  # ✅ correct linkage

        if appointment.staff != staff:
            raise PermissionDenied("You are not assigned to this patient's appointment.")

        serializer.save(staff_id=staff)



# -------------------------
# PrescriptionLab ViewSet
# -------------------------
class PrescriptionLabViewSet(NoUpdateDeleteMixin, StaffFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = PrescriptionLab.objects.all()
    serializer_class = PrescriptionLabSerializer
    permission_classes = [IsAuthenticated, IsDoctor, IsAssignedDoctor]

    def perform_create(self, serializer):
        """Auto-assign staff_id from request user"""
        staff = self.request.user.staff_profile
        consultation = serializer.validated_data.get("consultation_id")
        appointment = consultation.appointment_id

        if appointment.staff != staff:
            raise PermissionDenied("You are not assigned to this patient's appointment.")

        serializer.save(staff_id=staff)

class DoctorAppointmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Doctors can view only appointments assigned to them by receptionists.
    """
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "staff_profile"):
            return Appointment.objects.filter(staff=user.staff_profile).order_by("appoinment_date", "appoinment_time")
        return Appointment.objects.none()