from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import date
from rest_framework.decorators import api_view, permission_classes

from rest_framework.exceptions import PermissionDenied
from receptionist_api_app.models import Appointment
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
    Optional filter: ?date=YYYY-MM-DD
    """
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, "staff_profile"):
            return Appointment.objects.none()

        queryset = Appointment.objects.filter(staff=user.staff_profile)

        # Optional filter by date
        date_param = self.request.query_params.get("date")
        if date_param:
            queryset = queryset.filter(appoinment_date=date_param)

        return queryset.order_by("appoinment_date", "appoinment_time")



# -------------------------
# Dashboard Statistics Endpoint
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_dashboard_stats(request):
    """
    Returns dashboard statistics for the logged-in doctor:
    - Total appointments
    - Today's appointments
    - Total consultations done
    - Pending appointments
    """
    try:
        # Get the logged-in staff profile
        staff = request.user.staff_profile
        
        # Total appointments for this doctor
        total_appointments = Appointment.objects.filter(staff=staff).count()
        
        # Today's appointments
        today = date.today()
        today_appointments = Appointment.objects.filter(
            staff=staff,
            appoinment_date=today
        ).count()
        
        # Total consultations done by this doctor
        total_consultations = ConsultationNotes.objects.filter(staff_id=staff).count()
        
        # Pending appointments (status = 'Scheduled')
        pending_appointments = Appointment.objects.filter(
            staff=staff,
            appoinment_status='Scheduled'
        ).count()
        
        return Response({
            'totalAppointments': total_appointments,
            'todayAppointments': today_appointments,
            'totalConsultations': total_consultations,
            'pendingAppointments': pending_appointments
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )