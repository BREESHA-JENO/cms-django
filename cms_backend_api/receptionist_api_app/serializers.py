from rest_framework import serializers
from .models import Patient, ReceptionBilling, Appointment
from datetime import datetime
import re

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

    def validate_full_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name should have at least three characters.")
        return value

    def validate_date_of_birth(self, value):
        if value > datetime.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate_phone_number(self, value):
        if not re.match(r'^\d{10}$', value):
            raise serializers.ValidationError("Phone number should have 10 digits.")
        return value

class ReceptionBillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceptionBilling
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
