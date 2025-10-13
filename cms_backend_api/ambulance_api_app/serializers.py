from rest_framework import serializers
from .models import Ambulance, AmbulanceRequest

# Ambulance Serializer
class AmbulanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambulance
        fields = '__all__'


# Ambulance Request Serializer
class AmbulanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmbulanceRequest
        fields = '__all__'
        read_only_fields = ['request_time', 'status']
