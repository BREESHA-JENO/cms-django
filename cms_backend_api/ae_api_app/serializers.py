from rest_framework import serializers
from .models import TempPatient, AECase, EmergencyTreatment
from ambulance_api_app.models import Ambulance
from receptionist_api_app.models import Patient
from admin_api_app.models import Staff

# Temporary Patient Serializer
class TempPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempPatient
        fields = '__all__'


# AECase Serializer
class AECaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AECase
        fields = '__all__'
        read_only_fields = ['arrival_time', 'status']


# Emergency Treatment Serializer
class EmergencyTreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyTreatment
        fields = '__all__'
        read_only_fields = ['created_at', 'status']
