from rest_framework import serializers
from .models import Ambulance, AmbulanceRequest, Staff


class SimpleStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['id', 'name', 'user']

class AmbulanceSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.name', read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(queryset=Staff.objects.filter(user__role="AMB"), source='driver')

    class Meta:
        model = Ambulance
        fields = ['ambulance_id', 'vehicle_no', 'driver_id', 'driver_name', 'status']


class AmbulanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmbulanceRequest
        fields = '__all__'
        read_only_fields = ['request_time', 'status', 'completed_time']

    # ✅ Validate ambulance availability
    def validate(self, data):
        ambulance = data.get('assigned_ambulance')
        if ambulance and ambulance.status != 'Available':
            raise serializers.ValidationError("Selected ambulance is not available.")
        return data
