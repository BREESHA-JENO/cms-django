from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
import random, string
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import Staff, Specialization, WorkingDay, DoctorWorkingSchedule, DoctorDetails, LeaveRequest, ForgotPasswordRequest, Notification
from .serializers import (
    StaffSerializer,
    SpecializationSerializer,
    WorkingDaySerializer,
    DoctorWorkingScheduleSerializer,
    DoctorDetailsSerializer,
    LeaveRequestSerializer,
    ForgotPasswordRequestSerializer,
    NotificationSerializer,
)
from Authentication.permissions import IsAdmin, RolePermissionFactory , IsReceptionist
from rest_framework import permissions
from django.db.models import Q


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
        # Do NOT filter by is_active here.
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(user__role=role.upper())
        return queryset


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(serializer.errors)
            return Response(serializer.errors, status=400)
        serializer.is_valid(raise_exception=True)
        staff = serializer.save()
        data = serializer.data
        data["generated_password"] = staff.generated_password
        return Response(data, status=201)

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        roles = ['ADMIN', 'REC', 'DOC', 'LAB', 'PHARM', 'AMB']
        data = {}
        for role in roles:
            staff = self.get_queryset().filter(user__role=role)
            serializer = self.get_serializer(staff, many=True)
            data[role] = serializer.data
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        staff = self.get_object()
        staff.is_active = False
        staff.save()
        return Response({"status": "staff disabled"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        staff = self.get_object()
        staff.is_active = True
        staff.save()
        return Response({"status": "staff enabled"}, status=status.HTTP_200_OK)
    
    # in StaffViewSet

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        staff = self.get_queryset().filter(user=request.user).first()
        if staff is not None:
            serializer = self.get_serializer(staff)
            return Response(serializer.data)
        return Response({"detail": "Staff profile not found for this user."}, status=404)


# ----------------------------
# Specialization CRUD
# ----------------------------
class SpecializationViewSet(viewsets.ModelViewSet):
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [IsAuthenticated, RolePermissionFactory(["ADMIN"])]

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        specialization = self.get_object()
        specialization.is_active = False
        specialization.save()
        return Response({"status": "specialization disabled"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        specialization = self.get_object()
        specialization.is_active = True
        specialization.save()
        return Response({"status": "specialization enabled"}, status=status.HTTP_200_OK)


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
    queryset = LeaveRequest.objects.all().order_by("-requested_at")
    serializer_class = LeaveRequestSerializer

    def get_permissions(self):
        # Allow all authenticated users to list and create
        if self.action in ['list', 'create']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdmin]
        return [p() for p in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return LeaveRequest.objects.all().order_by("-requested_at")
        try:
            staff = Staff.objects.get(user=user)
            return LeaveRequest.objects.filter(staff=staff).order_by("-requested_at")
        except Staff.DoesNotExist:
            return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        staff = Staff.objects.get(user=self.request.user)
        leave = serializer.save(staff=staff)
        admins = User.objects.filter(role="ADMIN")
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="New Leave Request",
                message=f"{staff.name} has submitted a new leave request."
            )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        previous_status = instance.status
        response = super().update(request, *args, **kwargs)
        instance.refresh_from_db()
        if instance.status != previous_status:
            status_message = "approved" if instance.status == "APPROVED" else "rejected"
            Notification.objects.create(
                user=instance.staff.user,
                title="Leave Request Update",
                message=f"Your leave request from {instance.start_date} to {instance.end_date} has been {status_message}."
            )
        return response



class ForgotPasswordRequestViewSet(viewsets.ModelViewSet):
    queryset = ForgotPasswordRequest.objects.all()
    serializer_class = ForgotPasswordRequestSerializer

    def get_permissions(self):
        # Anyone can create forgot password requests (no login required)
        # Admin-only permission for other actions (approve/reject)
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request):
        staff_email = request.data.get('staff_email')  # use email only
        if not staff_email:
            return Response({'error': 'Email is required'}, status=400)

        try:
            staff = Staff.objects.get(Q(user__email=staff_email) | Q(user__username=staff_email))
        except Staff.DoesNotExist:
            return Response({'error': 'Username or email does not exist.'}, status=400)

        # Check for pending request
        if ForgotPasswordRequest.objects.filter(staff=staff, status='PENDING').exists():
            return Response({'error': 'A pending request already exists.'}, status=400)

        req = ForgotPasswordRequest.objects.create(staff=staff)
        serializer = self.get_serializer(req)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def update(self, request, pk=None):
        # Approve or reject forgot password request

        try:
            req = ForgotPasswordRequest.objects.get(pk=pk)
        except ForgotPasswordRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
        
        print(f"Approving forgot password for staff: {req.staff.name}, username: {req.staff.user.username}")

        action = request.data.get('action')  # expected 'approve' or 'reject'

        if action == 'approve':
            # Generate a new random password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user = req.staff.user
            user.password = make_password(new_password)
            user.save()

            req.status = 'APPROVED'
            req.processed_at = timezone.now()
            req.save()

            # Return new password only to admin - do NOT expose to user frontend
            return Response({
                'message': 'Password reset successful. New password generated.',
                'new_password': new_password
            })

        elif action == 'reject':
            req.status = 'REJECTED'
            req.processed_at = timezone.now()
            req.save()
            return Response({'message': 'Request rejected.'})

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        if not user.check_password(current_password):
            return Response({"current_password": ["Incorrect current password."]}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully."})
    
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Show only notifications for the logged-in user
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    # @action(detail=False, methods=["post"])
    # def mark_all_read(self, request):
    #     Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    #     return Response({"message": "All notifications marked as read"})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        print("User pk:", request.user.pk)
        print("Notifications to update:", Notification.objects.filter(user=request.user, is_read=False).values_list("id", flat=True))
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        print("Updated count:", updated)
        return Response({"message": "All notifications marked as read", "updated": updated})
