from rest_framework import serializers
from .models import Ambulance, AmbulanceRequest


class AmbulanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambulance
        fields = '__all__'

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
