from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.decorators import api_view, permission_classes

from rest_framework.exceptions import PermissionDenied
from receptionist_api_app.models import Appointment
from pharmacist_api_app.models import Medicine
from labtech_api_app.models import LabTest
from Authentication.permissions import IsDoctor
from .permissions import IsAssignedDoctor
from .serializers import DoctorAppointmentSerializer
from .models import ConsultationNotes, PrescriptionMed, PrescriptionLab, PrescriptionMedDetail, PrescriptionLabDetail
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

        # ✅ Save consultation
        consultation = serializer.save(staff_id=staff)
        
        # ✅ Mark appointment as COMPLETED after consultation
        appointment.appoinment_status = 'Completed'
        appointment.save()
        
        return consultation


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

        # Get consultations created in the last 24 hours
        last_24_hours = timezone.now() - timedelta(hours=24)
        consulted_recent_ids = list(ConsultationNotes.objects.filter(
            created_at__gte=last_24_hours
        ).values_list('appointment_id', flat=True))

        # Get ONLY SCHEDULED appointments for this doctor, excluding completed/cancelled
        queryset = Appointment.objects.filter(
            staff=user.staff_profile,
            appoinment_status='Scheduled'  # Only show scheduled appointments
        ).exclude(
            appointment_auto_id__in=consulted_recent_ids
        )

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
    - Total appointments to be consulted (future + present, not yet consulted)
    - Today's appointments to be consulted
    - Consultations done today
    - Pending appointments for today
    """
    try:
        # Get the logged-in staff profile
        staff = request.user.staff_profile
        # Use timezone-aware date to handle timezone correctly
        today = timezone.now().date()
        
        # Get appointment IDs that have been consulted TODAY
        consulted_today_ids = ConsultationNotes.objects.filter(
            created_at__date=today
        ).values_list('appointment_id', flat=True)
        
        # Total appointments to be consulted (scheduled, not yet consulted TODAY, today onwards)
        total_appointments_to_consult = Appointment.objects.filter(
            staff=staff,
            appoinment_date__gte=today,
            appoinment_status='Scheduled'
        ).exclude(
            appointment_auto_id__in=consulted_today_ids
        ).count()
        
        # Today's appointments to be consulted (not yet consulted TODAY)
        today_appointments_to_consult = Appointment.objects.filter(
            staff=staff,
            appoinment_date=today,
            appoinment_status='Scheduled'
        ).exclude(
            appointment_auto_id__in=consulted_today_ids
        ).count()
        
        # Consultations done today by this doctor
        today_consultations = ConsultationNotes.objects.filter(
            staff_id=staff,
            created_at__date=today
        ).count()
        
        # Pending appointments for today (scheduled but not consulted TODAY)
        pending_today = Appointment.objects.filter(
            staff=staff,
            appoinment_date=today,
            appoinment_status='Scheduled'
        ).exclude(
            appointment_auto_id__in=consulted_today_ids
        ).count()
        
        return Response({
            'totalAppointmentsToConsult': total_appointments_to_consult,
            'todayAppointmentsToConsult': today_appointments_to_consult,
            'todayConsultationsDone': today_consultations,
            'pendingToday': pending_today
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# -------------------------
# Doctor Medicines Endpoint (Read-only)
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_medicines(request):
    """
    Returns all medicines for doctors to prescribe.
    Read-only access to medicine list.
    """
    try:
        medicines = Medicine.objects.all().order_by('name')
        data = [{
            'med_auto_id': med.med_auto_id,
            'med_id': med.med_id,
            'name': med.name,
            'generic_name': med.generic_name,
            'description': med.description
        } for med in medicines]
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# -------------------------
# Doctor Lab Tests Endpoint (Read-only)
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_lab_tests(request):
    """
    Returns all lab tests for doctors to prescribe.
    Read-only access to lab test list.
    """
    try:
        tests = LabTest.objects.all().order_by('test_name')
        data = [{
            'Id': test.Id,
            'test_id': test.test_id,
            'test_name': test.test_name,
            'description': test.description,
            'price': str(test.price)
        } for test in tests]
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# -------------------------
# Patient Consultation History with Prescriptions
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_consultation_history(request, patient_id):
    """
    Returns complete consultation history for a specific patient including:
    - Consultation notes
    - Medicine prescriptions with details
    - Lab test prescriptions with details
    """
    try:
        from receptionist_api_app.models import Patient
        print(f"[DEBUG] Looking for patient: {patient_id}")
        
        
        # Verify patient exists
        patient = Patient.objects.filter(patient_id=patient_id).first()
        if not patient:
            print(f"[DEBUG] Patient {patient_id} not found")
            return Response({'error': f'Patient {patient_id} not found'}, status=status.HTTP_404_NOT_FOUND)
        
        print(f"[DEBUG] Patient found: {patient.patient_name}")
        
        # Get all appointments for this patient
        appointments = Appointment.objects.filter(patient_id=patient)
        print(f"[DEBUG] Found {appointments.count()} appointments")
        
        if appointments.count() == 0:
            return Response({
                'patient_id': patient.patient_id,
                'patient_name': patient.patient_name,
                'history': []
            }, status=status.HTTP_200_OK)
        
        appointment_ids = appointments.values_list('appointment_auto_id', flat=True)
        
        # Get all consultations for these appointments
        consultations = ConsultationNotes.objects.filter(
            appointment_id__in=appointment_ids
        ).select_related('appointment_id', 'staff_id').order_by('-created_at')
        
        print(f"[DEBUG] Found {consultations.count()} consultations")
        
        history_data = []
        for consultation in consultations:
            print(f"[DEBUG] Processing consultation: {consultation.consultation_id}")
            # Get medicine prescription (OneToOne relationship)
            med_data = []
            try:
                if hasattr(consultation, 'prescriptions_med'):
                    med_presc = consultation.prescriptions_med
                    print(f"[DEBUG] Found medicine prescription: {med_presc.prescription_med_id}")
                    # Get medicine details through the many-to-many relationship
                    from .models import PrescriptionMedDetail
                details = PrescriptionMedDetail.objects.filter(prescription=med_presc).select_related('medicine')
                med_data.append({
                    'prescription_id': med_presc.prescription_med_id,
                    'created_at': str(med_presc.created_at),
                    'medicines': [{
                        'medicine_id': detail.medicine.med_id,
                        'medicine_name': detail.medicine.name,
                        'dosage': detail.dosage,
                        'quantity': detail.quantity,
                        'instructions': detail.instructions or ''
                    } for detail in details]
                })
            except Exception as e:
                print(f"[DEBUG] Error loading medicine prescription: {str(e)}")
            # Get lab test prescriptions
            
            lab_data = []
            try:
                if hasattr(consultation, 'prescriptions_lab'):
                    lab_presc = consultation.prescriptions_lab
                    print(f"[DEBUG] Found lab prescription: {lab_presc.prescription_lab_id}")
                    # Get lab test details through the many-to-many relationship
                    details = PrescriptionLabDetail.objects.filter(prescription=lab_presc).select_related('lab_test')
                    if details.exists():
                        lab_data.append({
                            'prescription_id': lab_presc.prescription_lab_id,
                            'created_at': str(lab_presc.created_at),
                            'tests': [{
                                'test_id': detail.lab_test.test_id,
                                'test_name': detail.lab_test.test_name,
                                'instructions': detail.instructions or ''
                            } for detail in details]
                        })
            except Exception as e:
                print(f"[DEBUG] Error loading lab prescription: {str(e)}")
            
            # Build consultation record
            history_data.append({
                'consultation_id': consultation.consultation_id,
                'consultation_auto_id': consultation.consultation_auto_id,
                'appointment_id': consultation.appointment_id.appointment_id,
                'appointment_date': str(consultation.appointment_id.appoinment_date),
                'doctor_name': consultation.staff_id.name if consultation.staff_id else 'Unknown',
                'symptoms': consultation.symptoms or '',
                'diagnosis': consultation.diagnosis or '',
                'notes': consultation.notes or '',
                'created_at': str(consultation.created_at),
                'medicine_prescriptions': med_data,
                'lab_prescriptions': lab_data
            })
        
        print(f"[DEBUG] Returning {len(history_data)} consultation records")
        
        return Response({
            'patient_id': patient.patient_id,
            'patient_name': patient.patient_name,
            'history': history_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] in patient_consultation_history: {str(e)}")
        print(error_trace)
        return Response(
            {'error': str(e), 'traceback': error_trace},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

