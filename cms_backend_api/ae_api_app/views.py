from rest_framework import generics, status
from rest_framework.response import Response
from .models import TempPatient, AECase, EmergencyTreatment
from .serializers import TempPatientSerializer, AECaseSerializer, EmergencyTreatmentSerializer
from ambulance_api_app.models import Ambulance
from receptionist_api_app.models import Patient
from admin_api_app.models import Staff

# -----------------------------
# TempPatient Views
# -----------------------------
class TempPatientCreateView(generics.CreateAPIView):
    serializer_class = TempPatientSerializer
    queryset = TempPatient.objects.all()


class TempPatientListView(generics.ListAPIView):
    serializer_class = TempPatientSerializer
    queryset = TempPatient.objects.all()


# -----------------------------
# AECase Views
# -----------------------------
class AECaseCreateView(generics.CreateAPIView):
    serializer_class = AECaseSerializer
    queryset = AECase.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Auto-set patient_type based on whether patient or temp_patient is provided
        """
        data = request.data.copy()
        if data.get('patient'):
            data['patient_type'] = 'Permanent'
        elif data.get('temp_patient'):
            data['patient_type'] = 'Temporary'
        else:
            return Response({'error': 'Either patient or temp_patient must be provided.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AECaseListView(generics.ListAPIView):
    serializer_class = AECaseSerializer
    queryset = AECase.objects.all()


# Assign Ambulance to AECase
from rest_framework.decorators import api_view

@api_view(['POST'])
def assign_ambulance(request, ae_case_id):
    try:
        ae_case = AECase.objects.get(pk=ae_case_id)
        ambulance_id = request.data.get('ambulance_id')
        ambulance = Ambulance.objects.get(pk=ambulance_id)
    except AECase.DoesNotExist:
        return Response({'error': 'AECase not found'}, status=404)
    except Ambulance.DoesNotExist:
        return Response({'error': 'Ambulance not found'}, status=404)

    ae_case.ambulance = ambulance
    ae_case.brought_by = 'Ambulance'
    ae_case.save()

    # Change ambulance status to On Duty
    ambulance.status = 'On Duty'
    ambulance.save()

    return Response({'success': f'Ambulance {ambulance.vehicle_no} assigned to AECase {ae_case.ae_case_id}'})


# -----------------------------
# Emergency Treatment Views
# -----------------------------
class EmergencyTreatmentCreateView(generics.CreateAPIView):
    serializer_class = EmergencyTreatmentSerializer
    queryset = EmergencyTreatment.objects.all()


class EmergencyTreatmentListView(generics.ListAPIView):
    serializer_class = EmergencyTreatmentSerializer
    queryset = EmergencyTreatment.objects.all()


# Convert TempPatient to Permanent Patient
@api_view(['POST'])
def convert_temp_to_patient(request, temp_patient_id):
    try:
        temp = TempPatient.objects.get(pk=temp_patient_id)
    except TempPatient.DoesNotExist:
        return Response({'error': 'TempPatient not found'}, status=404)

    # Create permanent Patient record
    patient = Patient.objects.create(
        patient_name=temp.name,
        patient_age=temp.approx_age or 0,
        patient_gender=temp.gender or '',
        patient_email='',
        patient_phone=temp.emergency_contact or '',
        patient_blood_group='',
        patient_address='',
        patient_reg_date=None
    )

    # Update all AECase linked to this TempPatient
    AECase.objects.filter(temp_patient=temp).update(patient=patient, patient_type='Permanent', temp_patient=None)

    # Mark TempPatient as Merged
    temp.status = 'Merged'
    temp.save()

    return Response({'success': f'TempPatient {temp.temp_patient_id} converted to Patient {patient.patient_id}'})
