from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Ambulance, AmbulanceRequest
from .serializers import AmbulanceSerializer, AmbulanceRequestSerializer

# -----------------------------
# Ambulance Views
# -----------------------------
class AmbulanceCreateView(generics.CreateAPIView):
    serializer_class = AmbulanceSerializer
    queryset = Ambulance.objects.all()


class AmbulanceListView(generics.ListAPIView):
    serializer_class = AmbulanceSerializer
    queryset = Ambulance.objects.all()


class AmbulanceUpdateView(generics.UpdateAPIView):
    serializer_class = AmbulanceSerializer
    queryset = Ambulance.objects.all()
    lookup_field = 'pk'


# -----------------------------
# AmbulanceRequest Views
# -----------------------------
class AmbulanceRequestCreateView(generics.CreateAPIView):
    serializer_class = AmbulanceRequestSerializer
    queryset = AmbulanceRequest.objects.all()


class AmbulanceRequestListView(generics.ListAPIView):
    serializer_class = AmbulanceRequestSerializer
    queryset = AmbulanceRequest.objects.all()


@api_view(['POST'])
def update_request_status(request, request_id):
    """
    Update the status of an ambulance request
    """
    try:
        req = AmbulanceRequest.objects.get(pk=request_id)
    except AmbulanceRequest.DoesNotExist:
        return Response({'error': 'AmbulanceRequest not found'}, status=404)

    status_value = request.data.get('status')
    if status_value not in ['Pending', 'Assigned', 'Completed', 'Cancelled']:
        return Response({'error': 'Invalid status value'}, status=400)

    req.status = status_value
    req.save()

    # If completed or cancelled, mark ambulance as Available
    if req.assigned_ambulance and status_value in ['Completed', 'Cancelled']:
        ambulance = req.assigned_ambulance
        ambulance.status = 'Available'
        ambulance.save()

    return Response({'success': f'Request {req.request_id} status updated to {status_value}'})
