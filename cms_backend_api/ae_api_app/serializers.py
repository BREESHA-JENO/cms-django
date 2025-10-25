from rest_framework import serializers
from .models import TempPatient, AECase, EmergencyTreatment
from receptionist_api_app.models import Patient
from ambulance_api_app.models import Ambulance
from admin_api_app.models import Staff


# Temporary Patient Serializer
class TempPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempPatient
        fields = [
            'temp_patient_id',
            'temp_patient_code',
            'name',
            'approx_age',
            'gender',
            'description',
            'identification_marks',
            'emergency_contact',
            'status',
            'created_at'
        ]
        read_only_fields = ['temp_patient_id', 'temp_patient_code', 'created_at', 'status']

    def validate_emergency_contact(self, value):
        """Validate phone number format"""
        if value and not value.isdigit():
            raise serializers.ValidationError("Emergency contact must contain only digits")
        if value and (len(value) < 10 or len(value) > 15):
            raise serializers.ValidationError("Emergency contact must be between 10-15 digits")
        return value

    def validate(self, data):
        """Minimal validation for emergency cases"""
        # Allow submission with minimal data - it's an emergency!
        # As long as we have something (name defaults to 'Unknown'), accept it
        return data


# AECase Serializer
class AECaseSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    temp_patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AECase
        fields = [
            'ae_case_id',
            'patient_type',
            'patient',
            'patient_name',
            'temp_patient',
            'temp_patient_name',
            'triage_level',
            'brought_by',
            'ambulance',
            'arrival_time',
            'status',
            'notes'
        ]
        read_only_fields = ['ae_case_id', 'arrival_time']

    def get_patient_name(self, obj):
        if obj.patient:
            return obj.patient.patient_name
        return None

    def get_temp_patient_name(self, obj):
        if obj.temp_patient:
            return f"{obj.temp_patient.temp_patient_code} - {obj.temp_patient.name}"
        return None


# Emergency Treatment Serializer
class EmergencyTreatmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmergencyTreatment
        fields = [
            'treatment_id',
            'ae_case',
            'doctor',
            'doctor_name',
            'diagnosis',
            'medicine_list',
            'lab_tests',
            'status',
            'created_at'
        ]
        read_only_fields = ['treatment_id', 'created_at']

    def get_doctor_name(self, obj):
        if obj.doctor:
            return obj.doctor.staff_name
        return None


# Serializer for Converting TempPatient to Permanent Patient
class ConvertToPermanentSerializer(serializers.Serializer):
    patient_name = serializers.CharField(max_length=255, required=True)
    patient_age = serializers.IntegerField(required=True, min_value=0, max_value=150)
    patient_gender = serializers.CharField(max_length=10, required=True)
    patient_email = serializers.EmailField(required=False, allow_blank=True)
    patient_phone = serializers.CharField(max_length=15, required=True)
    patient_blood_group = serializers.CharField(max_length=5, required=False, allow_blank=True)
    patient_address = serializers.CharField(required=False, allow_blank=True)

    def validate_patient_phone(self, value):
        """Validate phone number"""
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        if len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits")
        return value
