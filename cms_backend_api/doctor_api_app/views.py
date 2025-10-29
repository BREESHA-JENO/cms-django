from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from receptionist_api_app.models import Appointment
from pharmacist_api_app.models import Medicine
from labtech_api_app.models import LabTest
from Authentication.permissions import IsDoctor
from .permissions import IsAssignedDoctor
from .serializers import DoctorAppointmentSerializer
from .models import ConsultationNotes, PrescriptionMed, PrescriptionLab
from .serializers import (
    ConsultationNotesSerializer,
    PrescriptionMedSerializer,
    PrescriptionLabSerializer,
)
import logging

logger = logging.getLogger(__name__)


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
        try:
            # Get staff profile with error handling
            if not hasattr(self.request.user, 'staff_profile'):
                raise PermissionDenied("User does not have a staff profile.")
            
            staff = self.request.user.staff_profile
            if not staff:
                raise PermissionDenied("Staff profile not found.")
                
            appointment = serializer.validated_data.get("appointment_id")
            if not appointment:
                raise ValidationError("Appointment ID is required.")

            # ✅ Check that this doctor is assigned to this appointment
            if appointment.staff != staff:
                raise PermissionDenied("You are not assigned to this patient's appointment.")

            # ✅ Save consultation
            consultation = serializer.save(staff_id=staff)
            
            # ✅ Mark appointment as COMPLETED after consultation
            appointment.appoinment_status = 'Completed'
            appointment.save()
            
            return consultation
            
        except Exception:
            raise


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
        # Determine today's date and appointments already consulted today by this doctor
        today = timezone.now().date()
        consulted_today_ids = list(ConsultationNotes.objects.filter(
            staff_id=user.staff_profile,
            created_at__date=today
        ).values_list('appointment_id', flat=True))

        # Start with scheduled appointments assigned to this doctor
        queryset = Appointment.objects.filter(
            staff=user.staff_profile,
            appoinment_status='Scheduled'
        )

        # Optional filter by date (YYYY-MM-DD)
        date_param = self.request.query_params.get("date")
        if date_param:
            queryset = queryset.filter(appoinment_date=date_param)

            # If caller requested today's appointments, exclude those already consulted today
            try:
                if str(today) == str(date_param):
                    queryset = queryset.exclude(appointment_auto_id__in=consulted_today_ids)
            except Exception:
                # If any parsing problems occur, fall back to the unmodified queryset
                pass

        # When no date param is provided, return all scheduled appointments (do not exclude by consulted_today_ids)
        return queryset.order_by("appoinment_time")



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
        
        # Compute breakdown counts for today's appointments (dynamic 'today' above)
        # We use the dashboard semantics from the reference/attachment:
        # - todayTotalAppointments = Scheduled + Completed (for appointment_date == today)
        # - todayConsulted = number of appointments with status == 'Completed' (for today)
        # - todayRemaining = number of appointments with status == 'Scheduled' (for today)
        scheduled_count = Appointment.objects.filter(
            staff=staff,
            appoinment_date=today,
            appoinment_status='Scheduled'
        ).count()

        completed_count = Appointment.objects.filter(
            staff=staff,
            appoinment_date=today,
            appoinment_status='Completed'
        ).count()

        cancelled_count = Appointment.objects.filter(
            staff=staff,
            appoinment_date=today,
            appoinment_status='Cancelled'
        ).count()

        # Today's total appointments: sum of Scheduled + Completed for today
        today_total = scheduled_count + completed_count

        # For the dashboard we treat 'consulted today' as appointments marked Completed for today
        today_consulted = completed_count

        # Remaining appointments for today are those still Scheduled
        today_remaining = scheduled_count

        # Compute other status bucket from true total (for debugging)
        total_all_today = Appointment.objects.filter(
            staff=staff,
            appoinment_date=today
        ).count()
        other_status_count = total_all_today - (scheduled_count + completed_count + cancelled_count)
        if other_status_count < 0:
            other_status_count = 0

        # Tomorrow's total scheduled appointments (only Scheduled status)
        from datetime import timedelta
        tomorrow = today + timedelta(days=1)
        tomorrow_total = Appointment.objects.filter(
            staff=staff,
            appoinment_date=tomorrow,
            appoinment_status='Scheduled'
        ).count()

        # Log computed values for quick server-side verification
        try:
            logger.info(
                "[doctor_dashboard_stats] staff=%s todayTotal=%s scheduled=%s completed=%s cancelled=%s other=%s todayConsulted=%s todayRemaining=%s tomorrow=%s",
                getattr(staff, 'pk', staff),
                today_total,
                scheduled_count,
                completed_count,
                cancelled_count,
                other_status_count,
                today_consulted,
                today_remaining,
                tomorrow_total,
            )
        except Exception:
            pass

        return Response({
            'todayTotalAppointments': today_total,
            'todayConsulted': today_consulted,
            'todayRemaining': today_remaining,
            'tomorrowAppointments': tomorrow_total,
            # breakdown for debugging/consistency checks
            'scheduledToday': scheduled_count,
            'completedToday': completed_count,
            'cancelledToday': cancelled_count,
            'otherStatusToday': other_status_count,
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
        # LabTest model fields are named with 'LabTestName' and 'LabTestId'
        tests = LabTest.objects.all().order_by('LabTestName')
        data = [{
            'Id': test.Id,
            'test_id': test.LabTestId,
            'test_name': test.LabTestName,
            'description': getattr(test, 'description', ''),
            'price': str(getattr(test, 'Rate', '0'))
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
    - Optional month filter: ?month=YYYY-MM
    """
    try:
        from receptionist_api_app.models import Patient
    # Debug prints removed
        
        
        # Verify patient exists. Support multiple incoming id formats:
        # - patient.patient_id (string code, e.g. P001)
        # - patient.patient_code (alternate code)
        # - patient.patient_auto_id (numeric PK)
        patient = Patient.objects.filter(patient_id=patient_id).first()
        if not patient:
            # try patient_code
            patient = Patient.objects.filter(patient_code=patient_id).first()
        if not patient:
            # if passed value looks numeric, try numeric PK lookup
            try:
                if str(patient_id).isdigit():
                    patient = Patient.objects.filter(patient_auto_id=int(patient_id)).first()
            except Exception:
                patient = None

        # Fallback: if caller passed an appointment_auto_id instead of a patient id,
        # try to resolve patient through the appointment record
        if not patient:
            try:
                appt = Appointment.objects.filter(appointment_auto_id=patient_id).select_related('patient_id').first()
                if appt:
                    patient = appt.patient_id
                    # Debug prints removed
            except Exception:
                # Debug prints removed
                pass

        if not patient:
            # Debug prints removed
            return Response({'error': f'Patient {patient_id} not found'}, status=status.HTTP_404_NOT_FOUND)
        
    # Debug prints removed
        
        # Get all appointments for this patient
        appointments = Appointment.objects.filter(patient_id=patient)
    # Debug prints removed
        
        if appointments.count() == 0:
            return Response({
                'patient_id': patient.patient_id,
                'patient_name': patient.patient_name,
                'history': []
            }, status=status.HTTP_200_OK)
        
        appointment_ids = appointments.values_list('appointment_auto_id', flat=True)
        
        # Get all consultations for these appointments
        consultations_query = ConsultationNotes.objects.filter(
            appointment_id__in=appointment_ids
        ).select_related('appointment_id', 'staff_id')
        
        # Apply month filter if provided
        month_param = request.GET.get('month')
        if month_param:
            try:
                # Parse YYYY-MM format
                year, month = map(int, month_param.split('-'))
                consultations_query = consultations_query.filter(
                    created_at__year=year,
                    created_at__month=month
                )
                # Debug prints removed
            except (ValueError, TypeError):
                # Debug prints removed
                pass
        
        consultations = consultations_query.order_by('-created_at')
        
    # Debug prints removed
        
        history_data = []
        for consultation in consultations:
            # Debug prints removed
            # Get medicine prescription (OneToOne relationship)
            med_data = []
            try:
                # Access OneToOne reverse relation safely
                try:
                    med_presc = consultation.prescriptions_med
                except PrescriptionMed.DoesNotExist:
                    med_presc = None

                if med_presc:
                    # Debug prints removed
                    # Get medicine details through the many-to-many through model
                    from .models import PrescriptionMedDetail
                    details = PrescriptionMedDetail.objects.filter(prescription=med_presc).select_related('medicine')
                    med_data.append({
                        'prescription_id': med_presc.prescription_med_id,
                        'created_at': str(med_presc.created_at),
                        'medicines': [{
                            'medicine_id': (detail.medicine.med_id if detail.medicine else None),
                            'medicine_name': (detail.medicine.name if detail.medicine else None) or detail.custom_medicine_name,
                            'dosage': detail.dosage,
                            'quantity': detail.quantity,
                            'instructions': detail.instructions or ''
                        } for detail in details]
                    })
                else:
                    # No prescription record for this consultation
                    pass
            except Exception:
                # Debug prints removed
                pass
            # Get lab test prescriptions
            
            lab_data = []
            try:
                try:
                    lab_presc = consultation.prescriptions_lab
                except PrescriptionLab.DoesNotExist:
                    lab_presc = None

                if lab_presc:
                    # Debug prints removed
                    from .models import PrescriptionLabDetail
                    details = PrescriptionLabDetail.objects.filter(prescription=lab_presc).select_related('lab_test')
                    # Include multiple key names to remain compatible with various frontend expectations
                    lab_tests_list = []
                    for detail in details:
                        lab_test = detail.lab_test
                        lab_tests_list.append({
                            'Id': getattr(lab_test, 'Id', None),
                            'LabTestId': getattr(lab_test, 'LabTestId', None),
                            'test_id': getattr(lab_test, 'LabTestId', None) or None,
                            'test_name': (getattr(lab_test, 'LabTestName', None) or detail.custom_lab_test_name),
                            # Provide the exact field name used elsewhere in the frontend
                            'LabTestName': getattr(lab_test, 'LabTestName', None) or detail.custom_lab_test_name,
                            'instructions': detail.instructions or ''
                        })

                    lab_data.append({
                        'prescription_id': lab_presc.prescription_lab_id,
                        'created_at': str(lab_presc.created_at),
                        'tests': lab_tests_list
                    })
                else:
                    pass
            except Exception:
                # Debug prints removed
                pass
            
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
        
    # Debug prints removed
        
        return Response({
            'patient_id': patient.patient_id,
            'patient_name': patient.patient_name,
            'history': history_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
    # Debug prints removed
        return Response(
            {'error': str(e), 'traceback': error_trace},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

