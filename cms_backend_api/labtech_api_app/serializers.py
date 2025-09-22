from rest_framework import serializers
from .models import LabTestCategory,LabTest,LabResult,LabBilling

class LabTestCategorySerializer(serializers.ModelSerializer):
    class Meta: 
        model = LabTestCategory
        fields = '__all__'

class LabTestSerializer(serializers.ModelSerializer):
    class Meta: 
        model = LabTest
        fields = '__all__'

class LabResultSerializer(serializers.ModelSerializer):
    class Meta: 
        model = LabResult
        fields = '__all__'

class LabBillingSerializer(serializers.ModelSerializer):
    class Meta: 
        model = LabBilling
        fields = '__all__'