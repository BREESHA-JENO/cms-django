# ambulance_api_app/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Ambulance, AmbulanceRequest
from .serializers import AmbulanceSerializer, AmbulanceRequestSerializer
from Authentication.permissions import IsAdmin, RolePermissionFactory, IsReceptionist
from admin_api_app.models import Staff

# -----------------------------
# Ambulance CRUD (Admin only)
# -----------------------------
class AmbulanceCreateView(generics.CreateAPIView):
    serializer_class = AmbulanceSerializer
    queryset = Ambulance.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class AmbulanceListView(generics.ListAPIView):
    serializer_class = AmbulanceSerializer
    queryset = Ambulance.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class AmbulanceUpdateView(generics.UpdateAPIView):
    serializer_class = AmbulanceSerializer
    queryset = Ambulance.objects.all()
    lookup_field = 'pk'
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


# -----------------------------
# AmbulanceRequest Views
# -----------------------------
class AmbulanceRequestCreateView(generics.CreateAPIView):
    """
    Receptionist can create a request.
    """
    serializer_class = AmbulanceRequestSerializer
    queryset = AmbulanceRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsReceptionist]

    def perform_create(self, serializer):
        staff = Staff.objects.get(user=self.request.user)
        serializer.save(created_by=staff)


class AmbulanceRequestListView(generics.ListAPIView):
    """
    Admin can view all requests.
    Receptionist can view their own requests.
    """
    serializer_class = AmbulanceRequestSerializer
    queryset = AmbulanceRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'REC':
            staff = Staff.objects.get(user=user)
            return AmbulanceRequest.objects.filter(created_by=staff)
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
    req.save()

    # Automatically free up ambulance when completed/cancelled
    if req.assigned_ambulance and status_value in ['Completed', 'Cancelled']:
        ambulance = req.assigned_ambulance
        ambulance.status = 'Available'
        ambulance.save()

    return Response({'success': f'Request {req.request_id} status updated to {status_value}'})
