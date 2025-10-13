from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Staff, Specialization, WorkingDay, DoctorWorkingSchedule, DoctorDetails, LeaveRequest
from .serializers import (
    StaffSerializer,
    SpecializationSerializer,
    WorkingDaySerializer,
    DoctorWorkingScheduleSerializer,
    DoctorDetailsSerializer,
    LeaveRequestSerializer,
)
from Authentication.permissions import IsAdmin, RolePermissionFactory , IsReceptionist
from rest_framework import permissions

User = get_user_model()


# ----------------------------
# Admin Dashboard
# ----------------------------
class AdminDashboard(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({"message": "Welcome Admin!"})


# ----------------------------
# Staff CRUD
# ----------------------------
class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, RolePermissionFactory(["ADMIN"])]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(user__role=role.upper())
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = serializer.save()
        data = serializer.data
        data["generated_password"] = staff.generated_password
        return Response(data, status=201)

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        roles = ['ADMIN', 'REC', 'DOC', 'LAB', 'PHARM']
        data = {}
        for role in roles:
            staff = self.get_queryset().filter(user__role=role)
            serializer = self.get_serializer(staff, many=True)
            data[role] = serializer.data
        return Response(data)


# ----------------------------
# Specialization CRUD
# ----------------------------
class SpecializationViewSet(viewsets.ModelViewSet):
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [IsAuthenticated, RolePermissionFactory(["ADMIN"])]


# ----------------------------
# WorkingDay CRUD
# ----------------------------
class WorkingDayViewSet(viewsets.ModelViewSet):
    queryset = WorkingDay.objects.all()
    serializer_class = WorkingDaySerializer
    permission_classes = [IsAuthenticated, RolePermissionFactory(["ADMIN"])]


# ----------------------------
# DoctorDetails CRUD
# ----------------------------
class DoctorDetailsViewSet(viewsets.ModelViewSet):
    queryset = DoctorDetails.objects.select_related("staff", "specialization").prefetch_related("schedules__day")
    serializer_class = DoctorDetailsSerializer
    permission_classes = [IsAuthenticated, RolePermissionFactory(["ADMIN"])]

    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get("staff_id")
        if staff_id:
            queryset = queryset.filter(staff__id=staff_id)
        return queryset


# ----------------------------
# DoctorWorkingSchedule CRUD
# ----------------------------
class DoctorWorkingScheduleViewSet(viewsets.ModelViewSet):
    queryset = DoctorWorkingSchedule.objects.all()
    serializer_class = DoctorWorkingScheduleSerializer
    permission_classes = [IsAuthenticated, RolePermissionFactory(["ADMIN"])]

    def get_queryset(self):
        queryset = super().get_queryset()
        doctor_id = self.request.query_params.get("doctor_id")
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated, IsReceptionist]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdmin]
        return [p() for p in permission_classes]

    def perform_create(self, serializer):
        staff = Staff.objects.get(user=self.request.user)
        serializer.save(staff=staff)