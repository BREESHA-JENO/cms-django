from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ConsultationNotes, PrescriptionMed, PrescriptionLab
from .serializers import (
    ConsultationNotesSerializer,
    PrescriptionMedSerializer,
    PrescriptionLabSerializer
)


# -------------------------
# Common mixin for disabling updates & deletes
# -------------------------
class NoUpdateDeleteMixin:
    """Mixin to block update and delete operations."""

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Updates are not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Updates are not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Deletions are not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# -------------------------
# Mixin to filter queryset by logged-in staff
# -------------------------
class StaffFilteredQuerysetMixin:
    """Filters queryset to only objects belonging to the logged-in staff (unless superuser)."""

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if hasattr(user, "staff") and not user.is_superuser:
            return qs.filter(staff_id=user.staff_profile)
        return qs


# -------------------------
# ConsultationNotes ViewSet
# -------------------------
class ConsultationNotesViewSet(NoUpdateDeleteMixin, StaffFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = ConsultationNotes.objects.all()
    serializer_class = ConsultationNotesSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Auto-assign staff_id from request user"""
        serializer.save(staff_id=self.request.user.staff_profile)


# -------------------------
# PrescriptionMed ViewSet
# -------------------------
class PrescriptionMedViewSet(NoUpdateDeleteMixin, StaffFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = PrescriptionMed.objects.all()
    serializer_class = PrescriptionMedSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Auto-assign staff_id from request user"""
        serializer.save(staff_id=self.request.user.staff_profile)


# -------------------------
# PrescriptionLab ViewSet
# -------------------------
class PrescriptionLabViewSet(NoUpdateDeleteMixin, StaffFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = PrescriptionLab.objects.all()
    serializer_class = PrescriptionLabSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Auto-assign staff_id from request user"""
        serializer.save(staff_id=self.request.user.staff_profile)
