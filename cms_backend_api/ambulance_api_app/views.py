from rest_framework import generics, status, permissions,viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Ambulance, AmbulanceRequest
from .serializers import AmbulanceSerializer, AmbulanceRequestSerializer
from Authentication.permissions import IsAdmin, IsReceptionist
from admin_api_app.models import Staff
from django.utils import timezone
from Authentication.permissions import RolePermissionFactory

# -----------------------------
# Ambulance CRUD (Admin only)
# ------------------------------
class AmbulanceViewSet(viewsets.ModelViewSet):
    queryset = Ambulance.objects.all()
    serializer_class = AmbulanceSerializer
    lookup_field = "ambulance_id"

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated(), RolePermissionFactory(['ADMIN', 'REC', 'AMB'])()]
        return [permissions.IsAuthenticated(), IsAdmin()]
# -----------------------------
# Ambulance Request Views
# -----------------------------
class AmbulanceRequestCreateView(generics.CreateAPIView):
    """
    Receptionist can create a request.
    """
    serializer_class = AmbulanceRequestSerializer
    queryset = AmbulanceRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsReceptionist]

    def perform_create(self, serializer):
        staff = Staff.objects.get(user=self.request.user)  # Receptionist creating
        ambulance = serializer.validated_data.get('assigned_ambulance')
        assigned_driver = None
        if ambulance is not None:
            assigned_driver = ambulance.driver  # FK to Staff
        serializer.save(
            created_by=staff,
            assigned_driver=assigned_driver
        )



class AmbulanceRequestListView(generics.ListAPIView):
    """
    Admin can view all requests.
    Receptionist can view their own.
    Drivers can view assigned requests.
    """
    serializer_class = AmbulanceRequestSerializer
    queryset = AmbulanceRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        staff = Staff.objects.get(user=user)
        if user.role == 'REC':
            return AmbulanceRequest.objects.filter(created_by=staff)
        elif user.role == 'AMB':  # ✅ Added driver view
            return AmbulanceRequest.objects.filter(assigned_driver=staff)
        return AmbulanceRequest.objects.all()


@api_view(['POST'])
def update_request_status(request, request_id):
    """
    Admin can update request status and manage ambulance availability.
    """
    if not request.user.role == 'ADMIN':
        return Response({'error': 'Only Admins can update request status'}, status=403)

    try:
        req = AmbulanceRequest.objects.get(pk=request_id)
    except AmbulanceRequest.DoesNotExist:
        return Response({'error': 'AmbulanceRequest not found'}, status=404)

    status_value = request.data.get('status')
    if status_value not in ['Pending', 'Assigned', 'Completed', 'Cancelled']:
        return Response({'error': 'Invalid status value'}, status=400)

    req.status = status_value

    # ✅ Automatically update ambulance status
    if req.assigned_ambulance:
        ambulance = req.assigned_ambulance

        if status_value == 'Assigned':
            ambulance.status = 'On Duty'
            ambulance.save()

        elif status_value in ['Completed', 'Cancelled']:
            ambulance.status = 'Available'
            ambulance.save()
            if status_value == 'Completed':
                req.completed_time = timezone.now()

    req.save()
    return Response({'success': f'Request {req.request_id} status updated to {status_value}'})
