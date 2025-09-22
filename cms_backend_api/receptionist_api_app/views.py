from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Patient
from .serializers import PatientSerializer

class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.filter(is_active=True)
    serializer_class = PatientSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            'message': 'Successfully added',
            'patient_reg_number': response.data.get('id'),
            'data': response.data
        }
        return response

class PatientRetrieveUpdateDisableView(generics.RetrieveUpdateAPIView):
    queryset = Patient.objects.filter(is_active=True)
    serializer_class = PatientSerializer

    def patch(self, request, *args, **kwargs):
        patient = self.get_object()

        if 'disable' in request.data:
            disable = request.data.get('disable')
            if disable:
                patient.is_active = False
                patient.save()
                return Response({'message': 'Successfully disabled'})

        # Restrict edits to only name and address
        allowed_fields = ['full_name', 'address']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        serializer = self.get_serializer(patient, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Updated successfully'})

class SearchPatientView(APIView):
    def get(self, request):
        reg_number = request.query_params.get('reg_number')
        phone_number = request.query_params.get('phone_number')

        if reg_number:
            try:
                patient = Patient.objects.get(id=reg_number, is_active=True)
                serializer = PatientSerializer(patient)
                return Response(serializer.data)
            except Patient.DoesNotExist:
                return Response({'message': 'Patient does not exist'}, status=status.HTTP_404_NOT_FOUND)
        elif phone_number:
            try:
                patient = Patient.objects.get(phone_number=phone_number, is_active=True)
                serializer = PatientSerializer(patient)
                return Response(serializer.data)
            except Patient.DoesNotExist:
                return Response({'message': 'Patient does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message': 'Provide either reg_number or phone_number'}, status=status.HTTP_400_BAD_REQUEST)
