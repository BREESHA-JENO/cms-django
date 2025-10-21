from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
import random, string
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Staff, Specialization, WorkingDay, DoctorWorkingSchedule, DoctorDetails, LeaveRequest, ForgotPasswordRequest
from .serializers import (
    StaffSerializer,
    SpecializationSerializer,
    WorkingDaySerializer,
    DoctorWorkingScheduleSerializer,
    DoctorDetailsSerializer,
    LeaveRequestSerializer,
    ForgotPasswordRequestSerializer
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
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdmin]
        return [p() for p in permission_classes]

    def perform_create(self, serializer):
        staff = Staff.objects.get(user=self.request.user)
        serializer.save(staff=staff)

class ForgotPasswordRequestViewSet(viewsets.ModelViewSet):
    queryset = ForgotPasswordRequest.objects.all()
    serializer_class = ForgotPasswordRequestSerializer

    def create(self, request):
        # staff submits a forgot password request
        staff_id = request.data.get('staff_id')
        reason = request.data.get('reason', '')

        try:
            staff = Staff.objects.get(staff_id=staff_id)
        except Staff.DoesNotExist:
            return Response({'error': 'Invalid staff ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent duplicate pending requests
        if ForgotPasswordRequest.objects.filter(staff=staff, status='PENDING').exists():
            return Response({'error': 'A pending request already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        req = ForgotPasswordRequest.objects.create(staff=staff, reason=reason)
        return Response({'message': 'Request submitted successfully.'}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        # admin approves/rejects
        try:
            req = ForgotPasswordRequest.objects.get(pk=pk)
        except ForgotPasswordRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # "approve" or "reject"

        if action == 'approve':
            # generate new random password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user = req.staff.user
            user.password = make_password(new_password)
            user.save()

            req.status = 'APPROVED'
            req.processed_at = timezone.now()
            req.save()

            return Response({
                'message': f'Password reset successful. New password generated.',
                'new_password': new_password  # You can log/send via email, don’t expose to frontend directly
            })

        elif action == 'reject':
            req.status = 'REJECTED'
            req.processed_at = timezone.now()
            req.save()
            return Response({'message': 'Request rejected.'})

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)