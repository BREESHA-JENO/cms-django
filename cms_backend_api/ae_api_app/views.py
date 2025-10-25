from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import TempPatient, AECase, EmergencyTreatment
from .serializers import (
    TempPatientSerializer, 
    AECaseSerializer, 
    EmergencyTreatmentSerializer,
    ConvertToPermanentSerializer
)
from receptionist_api_app.models import Patient
from ambulance_api_app.models import Ambulance
from Authentication.permissions import IsReceptionist


# ==============================
# TEMPORARY PATIENT VIEWS
# ==============================

class TempPatientCreateView(generics.CreateAPIView):
    """Create a new temporary patient"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = TempPatientSerializer
    queryset = TempPatient.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'message': f"Temporary Patient {serializer.data['temp_patient_code']} registered successfully",
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class TempPatientListView(generics.ListAPIView):
    """List all temporary patients"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = TempPatientSerializer
    queryset = TempPatient.objects.all().order_by('-created_at')

    def get_queryset(self):
        queryset = TempPatient.objects.all().order_by('-created_at')
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(temp_patient_code__icontains=search) |
                Q(name__icontains=search) |
                Q(emergency_contact__icontains=search)
            )
        
        return queryset


class TempPatientDetailView(generics.RetrieveAPIView):
    """Get details of a specific temporary patient"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = TempPatientSerializer
    queryset = TempPatient.objects.all()
    lookup_field = 'temp_patient_id'


class TempPatientUpdateView(generics.UpdateAPIView):
    """Update temporary patient details"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = TempPatientSerializer
    queryset = TempPatient.objects.all()
    lookup_field = 'temp_patient_id'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if instance.status == 'Merged':
            return Response({
                'error': 'Cannot update a merged patient. This patient has been converted to permanent.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': f"Temporary Patient {instance.temp_patient_code} updated successfully",
            'data': serializer.data
        })


class TempPatientDeleteView(generics.DestroyAPIView):
    """Delete temporary patient"""
    permission_classes = [IsAuthenticated]
    queryset = TempPatient.objects.all()
    lookup_field = 'temp_patient_id'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if AECase.objects.filter(temp_patient=instance).exists():
            return Response({
                'error': 'Cannot delete this temporary patient. Emergency cases are linked to this record.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        temp_code = instance.temp_patient_code
        self.perform_destroy(instance)
        
        return Response({
            'message': f"Temporary Patient {temp_code} deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_temp_to_permanent(request, temp_patient_id):
    """Convert temporary patient to permanent patient"""
    try:
        temp_patient = TempPatient.objects.get(pk=temp_patient_id)
    except TempPatient.DoesNotExist:
        return Response({'error': 'Temporary patient not found'}, status=status.HTTP_404_NOT_FOUND)

    if temp_patient.status == 'Merged':
        return Response({
            'error': 'This temporary patient has already been converted to permanent.'
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = ConvertToPermanentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data

    permanent_patient = Patient.objects.create(
        patient_name=validated_data['patient_name'],
        patient_age=validated_data['patient_age'],
        patient_gender=validated_data['patient_gender'],
        patient_email=validated_data.get('patient_email', ''),
        patient_phone=validated_data['patient_phone'],
        patient_blood_group=validated_data.get('patient_blood_group', ''),
        patient_address=validated_data.get('patient_address', ''),
    )

    ae_cases = AECase.objects.filter(temp_patient=temp_patient)
    ae_cases.update(
        patient=permanent_patient,
        patient_type='Permanent',
        temp_patient=None
    )

    temp_patient.status = 'Merged'
    temp_patient.save()

    return Response({
        'message': f'Temporary Patient {temp_patient.temp_patient_code} successfully converted to Permanent Patient {permanent_patient.patient_code}',
        'temp_patient_code': temp_patient.temp_patient_code,
        'permanent_patient_id': permanent_patient.patient_id,
        'permanent_patient_code': permanent_patient.patient_code,
        'ae_cases_transferred': ae_cases.count()
    }, status=status.HTTP_201_CREATED)


# ==============================
# AE CASE VIEWS
# ==============================

class AECaseCreateView(generics.CreateAPIView):
    """Create a new AE case"""
    permission_classes = [IsAuthenticated]
    serializer_class = AECaseSerializer
    queryset = AECase.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        if data.get('patient'):
            data['patient_type'] = 'Permanent'
        elif data.get('temp_patient'):
            data['patient_type'] = 'Temporary'
        else:
            return Response({
                'error': 'Either patient or temp_patient must be provided.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'message': f"AE Case {serializer.data['ae_case_id']} created successfully",
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class AECaseListView(generics.ListAPIView):
    """List all AE cases with filters"""
    permission_classes = [IsAuthenticated]
    serializer_class = AECaseSerializer
    queryset = AECase.objects.all().order_by('-arrival_time')

    def get_queryset(self):
        queryset = AECase.objects.all().order_by('-arrival_time')
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        triage = self.request.query_params.get('triage', None)
        if triage:
            queryset = queryset.filter(triage_level=triage)
        
        patient_type = self.request.query_params.get('patient_type', None)
        if patient_type:
            queryset = queryset.filter(patient_type=patient_type)
        
        return queryset


class AECaseDetailView(generics.RetrieveAPIView):
    """Get details of a specific AE case"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = AECaseSerializer
    queryset = AECase.objects.all()
    lookup_field = 'ae_case_id'


class AECaseUpdateView(generics.UpdateAPIView):
    """Update AE case details"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = AECaseSerializer
    queryset = AECase.objects.all()
    lookup_field = 'ae_case_id'


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsReceptionist])
def assign_ambulance(request, ae_case_id):
    """Assign ambulance to an AE case"""
    try:
        ae_case = AECase.objects.get(pk=ae_case_id)
    except AECase.DoesNotExist:
        return Response({'error': 'AE Case not found'}, status=status.HTTP_404_NOT_FOUND)

    ambulance_id = request.data.get('ambulance_id')
    if not ambulance_id:
        return Response({'error': 'ambulance_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        ambulance = Ambulance.objects.get(pk=ambulance_id)
    except Ambulance.DoesNotExist:
        return Response({'error': 'Ambulance not found'}, status=status.HTTP_404_NOT_FOUND)

    ae_case.ambulance = ambulance
    ae_case.brought_by = 'Ambulance'
    ae_case.save()

    ambulance.status = 'On Duty'
    ambulance.save()

    return Response({
        'message': f'Ambulance {ambulance.vehicle_no} assigned to AE Case {ae_case.ae_case_id}',
        'ae_case_id': ae_case.ae_case_id,
        'ambulance_vehicle_no': ambulance.vehicle_no
    })


# ==============================
# EMERGENCY TREATMENT VIEWS
# ==============================

class EmergencyTreatmentCreateView(generics.CreateAPIView):
    """Create emergency treatment record"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = EmergencyTreatmentSerializer
    queryset = EmergencyTreatment.objects.all()


class EmergencyTreatmentListView(generics.ListAPIView):
    """List all emergency treatments"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = EmergencyTreatmentSerializer
    queryset = EmergencyTreatment.objects.all().order_by('-created_at')


class EmergencyTreatmentDetailView(generics.RetrieveAPIView):
    """Get details of a specific treatment"""
    permission_classes = [IsAuthenticated, IsReceptionist]
    serializer_class = EmergencyTreatmentSerializer
    queryset = EmergencyTreatment.objects.all()
    lookup_field = 'treatment_id'

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsReceptionist])
def ae_case_search(request):
    """Search AE cases by query and status"""
    query = request.query_params.get('query', '')
    status_param = request.query_params.get('status', '')
    
    queryset = AECase.objects.all().order_by('-arrival_time')
    
    # Search by case ID or patient name
    if query:
        queryset = queryset.filter(
            Q(ae_case_id__icontains=query) |
            Q(patient__patient_name__icontains=query) |
            Q(temp_patient__name__icontains=query) |
            Q(temp_patient__temp_patient_code__icontains=query)
        )
    
    # Filter by status
    if status_param and status_param != 'all':
        queryset = queryset.filter(status=status_param)
    
    serializer = AECaseSerializer(queryset, many=True)
    return Response(serializer.data)
