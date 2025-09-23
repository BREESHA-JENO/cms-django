from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import LabTestCategory, LabTest, LabResult, LabBilling
from .serializers import (
    LabTestCategorySerializer,
    LabTestSerializer,
    LabResultSerializer,
    LabBillingSerializer,
)


class LabTestCategoryViewSet(viewsets.ModelViewSet):
    """CRUD for LabTestCategory"""
    queryset = LabTestCategory.objects.all()
    serializer_class = LabTestCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class LabTestViewSet(viewsets.ModelViewSet):
    """CRUD for LabTest"""
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer
    permission_classes = [permissions.IsAuthenticated]


class LabResultViewSet(viewsets.ModelViewSet):
    """CRUD for LabResult"""
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer
    permission_classes = [permissions.IsAuthenticated]


class LabBillingViewSet(viewsets.ModelViewSet):
    """CRUD for LabBilling"""
    queryset = LabBilling.objects.all()
    serializer_class = LabBillingSerializer
    permission_classes = [permissions.IsAuthenticated]
