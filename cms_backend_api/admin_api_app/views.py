from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Staff, Specialization, WorkingDay, DoctorWorkingSchedule, DoctorDetails
from .serializers import (
    StaffSerializer,
    SpecializationSerializer,
    WorkingDaySerializer,
    DoctorWorkingScheduleSerializer,
    DoctorDetailsSerializer,
)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(user__role=role.upper())  # e.g. ?role=DOC
        return queryset

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        """Return staff grouped by role"""
        roles = ['ADMIN', 'REC', 'DOC', 'LAB', 'PHARM']
        data = {}

        for role in roles:
            staff = self.get_queryset().filter(user__role=role)
            serializer = self.get_serializer(staff, many=True)
            data[role] = serializer.data

        return Response(data)

    def perform_create(self, serializer):
        serializer.save()


class SpecializationViewSet(viewsets.ModelViewSet):
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer


class WorkingDayViewSet(viewsets.ModelViewSet):
    queryset = WorkingDay.objects.all()
    serializer_class = WorkingDaySerializer


# ✅ New: Manage doctor details directly if needed
class DoctorDetailsViewSet(viewsets.ModelViewSet):
    queryset = DoctorDetails.objects.select_related("staff", "specialization").prefetch_related("schedules__day")
    serializer_class = DoctorDetailsSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get("staff_id")
        if staff_id:
            queryset = queryset.filter(staff__id=staff_id)
        return queryset

# ✅ New: Manage doctor working schedules (shifts)
class DoctorWorkingScheduleViewSet(viewsets.ModelViewSet):
    queryset = DoctorWorkingSchedule.objects.all()
    serializer_class = DoctorWorkingScheduleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        doctor_id = self.request.query_params.get("doctor_id")
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)  # ?doctor_id=5
        return queryset
