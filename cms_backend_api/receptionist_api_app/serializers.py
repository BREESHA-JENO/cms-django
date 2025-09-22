# receptionist_api_app/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import time
from .models import Patient, RecBilling, Appointment
from admin_api_app.models import Staff, DoctorWorkingSchedule  # assumes schedule model lives here

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['patient_auto_id', 'patient_created_at']

    def validate_patient_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Name should have at least three characters.")
        return value

    def validate_patient_reg_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Registration date cannot be in the future.")
        return value

    def validate_patient_phone(self, value):
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) < 10:
            raise serializers.ValidationError("Phone number should have at least 10 digits.")
        return value
    
    def validate_patient_gender(self, value):
        allowed = ['Male', 'Female', 'Other']  # or whatever codes you use
        if value.upper() not in allowed:
            raise serializers.ValidationError(
                "Gender must be one of: Male, Female or Other."
            )
        return value

    def validate_patient_blood_group(self, value):
        valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if value.upper() not in valid_groups:
            raise serializers.ValidationError(
                "Enter a valid blood group like A+, O-, etc."
            )
        return value

    def validate_patient_phone(self, value):
        # keep your existing check and tighten it
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) != 10:
            raise serializers.ValidationError(
                "Phone number must contain exactly 10 digits."
            )
        return value

    def validate_patient_address(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Address should have at least 5 characters."
            )
        return value

    def validate_patient_age(self, value):
        if value is None or value <= 0 or value > 120:
            raise serializers.ValidationError(
                "Age must be between 1 and 120."
            )
        return value

class PatientEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['patient_name', 'patient_address']

class PatientSearchSerializer(serializers.Serializer):
    patient_id = serializers.CharField(required=False)
    patient_phone = serializers.CharField(required=False)
    def validate(self, attrs):
        if not attrs.get('patient_id') and not attrs.get('patient_phone'):
            raise serializers.ValidationError("Provide patient_id or patient_phone.")
        return attrs

def next_app_code():
    last = Appointment.objects.order_by('-appointment_auto_id').first()
    if not last or not last.appointment_id or not last.appointment_id.startswith('APP'):
        return 'APP001'
    try:
        n = int(last.appointment_id.replace('APP', ''))
    except Exception:
        n = last.appointment_auto_id
    return f"APP{n+1:03d}"

# receptionist_api_app/serializers.py
class AppointmentSerializer(serializers.ModelSerializer):
    patient_code = serializers.CharField(write_only=True, required=True)
    appointment_id = serializers.CharField(read_only=True)

    class Meta:
        model = Appointment
        fields = ['appointment_auto_id','appointment_id','patient_id','patient_code','staff',
                  'appoinment_date','appoinment_time','appoinment_status','appoinment_created_at']
        read_only_fields = ['appointment_auto_id','appointment_id','appoinment_created_at']

    def validate(self, attrs):
        code = self.initial_data.get('patient_code')
        try:
            patient = Patient.objects.get(patient_id=code)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found.")
        attrs['patient_id'] = patient
        staff = attrs.get('staff')
        if not isinstance(staff, Staff) or staff.role != 'Doctor':
            raise serializers.ValidationError("Selected staff must be a Doctor.")
        d = attrs.get('appoinment_date')
        t = attrs.get('appoinment_time')
        if d < timezone.localdate():
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        weekday = d.weekday()
        qs = DoctorWorkingSchedule.objects.filter(doctor=staff, day_id=weekday)
        if not qs.exists():
            raise serializers.ValidationError("doctor not available today.")
        if not any(s.start_time <= t <= s.end_time for s in qs):
            raise serializers.ValidationError("doctor not available at selected time.")
        return attrs


class RecBillingSerializer(serializers.ModelSerializer):
    patient_code = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = RecBilling
        fields = ['rec_bill_id','patient_id','patient_code','staff','consultation_fee','billing_status','billing_created_at']
        read_only_fields = ['rec_bill_id','billing_created_at']

    def validate(self, attrs):
        code = self.initial_data.get('patient_code')
        try:
            patient = Patient.objects.get(patient_id=code)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found or inactive.")
        attrs['patient_id'] = patient

        staff = attrs.get('staff')
        if not isinstance(staff, Staff) or staff.role != 'Doctor':
            raise serializers.ValidationError("Billing staff must be a Doctor.")
        if attrs.get('consultation_fee', 0) < 0:
            raise serializers.ValidationError("consultation_fee cannot be negative.")
        return attrs
