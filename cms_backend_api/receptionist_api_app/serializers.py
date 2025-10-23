# receptionist_api_app/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import time
from .models import Patient, RecBilling, Appointment
from admin_api_app.models import Staff, DoctorWorkingSchedule
from django.utils import timezone


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['patient_auto_id', 'patient_created_at','patient_id']

    def validate_patient_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Name should have at least three characters.")
        return value

    def validate_patient_reg_date(self, value):
        today = timezone.localdate()
        if value > today:
            raise serializers.ValidationError("Registration date cannot be in the future.")
        return value

    def validate_patient_gender(self, value):
        allowed = ['Male', 'Female', 'Other']
        value_formatted = value.capitalize()
        if value_formatted not in allowed:
            raise serializers.ValidationError("Gender must be one of: Male, Female or Other.")
        return value_formatted

    def validate_patient_blood_group(self, value):
        valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        value_upper = value.upper()
        if value_upper not in valid_groups:
            raise serializers.ValidationError("Enter a valid blood group like A+, O-, etc.")
        return value_upper

    def validate_patient_phone(self, value):
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) != 10:
            raise serializers.ValidationError("Phone number must contain exactly 10 digits.")
        if not digits[0] in ['6', '7', '8', '9']:
            raise serializers.ValidationError("Phone number must start with 6, 7, 8, or 9.")
        return digits

    def validate_patient_address(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Address should have at least 5 characters.")
        return value

    def validate_patient_age(self, value):
        if value is None or value <= 0 or value > 120:
            raise serializers.ValidationError("Age must be between 1 and 120.")
        return value


class PatientEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['patient_name', 'patient_email', 'patient_age', 'patient_gender', 
                  'patient_blood_group', 'patient_phone', 'patient_address', 'is_active']
        read_only_fields = ['patient_id', 'patient_auto_id', 'patient_reg_date', 'patient_created_at']
    
    def validate_patient_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Name should have at least three characters.")
        return value.strip()

    def validate_patient_phone(self, value):
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) != 10:
            raise serializers.ValidationError("Phone number must contain exactly 10 digits.")
        if not digits[0] in ['6', '7', '8', '9']:
            raise serializers.ValidationError("Phone number must start with 6, 7, 8, or 9.")
        return digits

    def validate_patient_gender(self, value):
        value_formatted = value.capitalize()
        allowed = ['Male', 'Female', 'Other']
        if value_formatted not in allowed:
            raise serializers.ValidationError("Gender must be one of: Male, Female or Other.")
        return value_formatted

    def validate_patient_blood_group(self, value):
        value_upper = value.upper()
        valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if value_upper not in valid_groups:
            raise serializers.ValidationError("Enter a valid blood group like A+, O-, etc.")
        return value_upper

    def validate_patient_address(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Address should have at least 5 characters.")
        return value.strip()

    def validate_patient_age(self, value):
        if value is None or value <= 0 or value > 120:
            raise serializers.ValidationError("Age must be between 1 and 120.")
        return value


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


class AppointmentSerializer(serializers.ModelSerializer):
    patient_code = serializers.CharField(write_only=True, required=True)
    appointment_id = serializers.CharField(read_only=True)
    patient_name = serializers.CharField(source='patient_id.patient_name', read_only=True)
    doctor_name = serializers.CharField(source='staff.name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'appointment_auto_id', 'appointment_id', 'patient_id', 'patient_code',
            'patient_name', 'staff', 'doctor_name', 'appoinment_date',
            'appoinment_time', 'appoinment_status', 'appoinment_created_at'
        ]
        read_only_fields = ['appointment_auto_id', 'appointment_id', 'appoinment_created_at', 'patient_id']

    def create(self, validated_data):
        # Extract patient_code from validated data
        patient_code = validated_data.pop('patient_code')
        
        # Find the patient
        try:
            patient = Patient.objects.get(patient_id=patient_code)
        except Patient.DoesNotExist:
            raise serializers.ValidationError({"patient_code": "Patient not found."})
        
        # Add patient to validated data
        validated_data['patient_id'] = patient
        
        # Create and return the appointment
        return super().create(validated_data)

    def validate(self, attrs):
        # Get staff from attrs (already a Staff object from DRF)
        staff = attrs.get('staff')
        
        # Validate staff is a doctor
        if not isinstance(staff, Staff):
            raise serializers.ValidationError({"staff": "Invalid staff selected."})
        
        if staff.user.role != 'DOC':
            raise serializers.ValidationError({"staff": "Selected staff must be a Doctor."})
        
        # Validate date
        appointment_date = attrs.get('appoinment_date')
        if appointment_date < timezone.localdate():
            raise serializers.ValidationError({"appoinment_date": "Appointment date cannot be in the past."})
        
        # Optional: Check doctor availability (can be skipped if causing issues)
        appointment_time = attrs.get('appoinment_time')
        weekday = appointment_date.weekday()
        
        try:
            doctor_details = staff.doctor_details
            schedules = DoctorWorkingSchedule.objects.filter(
                doctor=doctor_details,
                day__id=weekday
            )
            
            if not schedules.exists():
                # Just a warning, don't block the appointment
                print(f"Warning: No schedule found for doctor {staff.name} on this day")
            else:
                # Check if time is within working hours
                time_valid = any(
                    s.start_time <= appointment_time <= s.end_time 
                    for s in schedules
                )
                if not time_valid:
                    print(f"Warning: Time {appointment_time} is outside working hours")
        except Exception as e:
            # If checking fails, just log it and continue
            print(f"Schedule check error: {e}")
        
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
        if not isinstance(staff, Staff) or staff.role != 'DOC':
            raise serializers.ValidationError("Billing staff must be a Doctor.")
        if attrs.get('consultation_fee', 0) < 0:
            raise serializers.ValidationError("consultation_fee cannot be negative.")
        return attrs

# Add this at the end of serializers.py
class DoctorSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='user.role', read_only=True)
    department = serializers.CharField(source='doctor_details.specialization.name', read_only=True, default='General')
    
    class Meta:
        model = Staff
        fields = ['id','staff_id', 'name', 'department', 'role', 'phone_number', 'email']