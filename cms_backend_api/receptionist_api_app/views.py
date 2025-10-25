# receptionist_api_app/views.py
from rest_framework import generics, viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from admin_api_app.models import Staff
from .serializers import DoctorSerializer
from rest_framework.decorators import api_view, permission_classes

from .models import Patient, Appointment, RecBilling
from .serializers import (
    PatientSerializer, PatientEditSerializer, PatientSearchSerializer,
    AppointmentSerializer, RecBillingSerializer,DoctorSerializer
)
from .permissions import IsReceptionist, IsDoctor, IsAdminOrStaff

# Patients
class PatientViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin):
    queryset = Patient.objects.all().order_by('-patient_created_at')
    permission_classes = [IsAuthenticated & IsReceptionist]

    def get_serializer_class(self):
        if self.action in ['partial_update', 'update']:
            return PatientEditSerializer
        return PatientSerializer

    def get_queryset(self):
        # No is_active in schema; return all patients
        return Patient.objects.all().order_by('-patient_created_at')

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        s = PatientSearchSerializer(data=request.query_params)
        s.is_valid(raise_exception=True)
        qs = self.get_queryset()
        pid = s.validated_data.get('patient_id')
        ph = s.validated_data.get('patient_phone')
        if pid:
            qs = qs.filter(patient_id__iexact=pid)
        if ph:
            qs = qs.filter(patient_phone=ph)
        return Response(PatientSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='disable')
    def disable(self, request, pk=None):
        # No soft delete flag available; acknowledge request without DB change.
        # If hard delete is desired, uncomment:
        # self.get_object().delete()
        return Response({'message': 'Disable not supported (no soft-delete field).'})

# Appointments
class AppointmentViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    queryset = Appointment.objects.select_related('patient_id','staff').all().order_by('-appoinment_created_at')
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated & IsReceptionist]

    @action(detail=True, methods=['patch'], url_path='status')
    def set_status(self, request, pk=None):
        appt = self.get_object()
        status_value = request.data.get('appoinment_status')
        if status_value not in dict(Appointment.STATUS_CHOICES):
            return Response({'detail':'Invalid status'}, status=400)
        appt.appoinment_status = status_value
        appt.save(update_fields=['appoinment_status'])
        return Response({'detail':'Status updated','appoinment_status': appt.appoinment_status})


# Read-only Doctor ViewSet for Receptionists
class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Receptionists can view doctor list for appointment scheduling
    """
    queryset = Staff.objects.filter(user__role='DOC', is_active=True).select_related('user','doctor_details__specialization').order_by('name')
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated & IsReceptionist]
# Doctor self view
class MyAppointmentsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Appointment.objects.select_related('patient_id','staff').all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated & IsDoctor & IsReceptionist]

    def get_queryset(self):
        # Assuming Staff is linked to User via OneToOne; map request.user to Staff
        try:
            staff = self.request.user.staff
        except Exception:
            return Appointment.objects.none()
        return super().get_queryset().filter(staff=staff)

# Billing


class RecBillingViewSet(viewsets.ModelViewSet):
    """
    Receptionists can manage billing records
    """
    queryset = RecBilling.objects.all()
    serializer_class = RecBillingSerializer
    permission_classes = [IsAuthenticated & IsReceptionist]
    
    # ✅ ADD THIS METHOD
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update billing payment status
        """
        billing = self.get_object()
        new_status = request.data.get('billing_status')
        
        if not new_status:
            return Response(
                {'error': 'billing_status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status choice
        valid_statuses = ['Paid', 'Unpaid', 'Partially Paid']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        billing.billing_status = new_status
        billing.save()
        
        serializer = self.get_serializer(billing)
        return Response(serializer.data)

from rest_framework.decorators import api_view, permission_classes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctors_for_ae(request):
    """Public endpoint for getting doctors list (for A&E module)"""
    doctors = Staff.objects.filter(user__role='DOC', is_active=True).select_related('user')
    serializer = DoctorSerializer(doctors, many=True)
    return Response(serializer.data)

