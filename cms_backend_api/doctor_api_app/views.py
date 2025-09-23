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
        return Response(
            {"detail": "Updates are not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Updates are not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Deletions are not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


# -------------------------
# ConsultationNotes ViewSet
# -------------------------
class ConsultationNotesViewSet(NoUpdateDeleteMixin, viewsets.ModelViewSet):
    queryset = ConsultationNotes.objects.all()
    serializer_class = ConsultationNotesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        If doctor logged in → return only their consultations.
        If admin/staff → return all.
        """
        user = self.request.user
        if hasattr(user, "staff"):  # if staff object exists
            return ConsultationNotes.objects.filter(staff_id=user.staff)
        return ConsultationNotes.objects.all()


# -------------------------
# PrescriptionMed ViewSet
# -------------------------
class PrescriptionMedViewSet(NoUpdateDeleteMixin, viewsets.ModelViewSet):
    serializer_class = PrescriptionMedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "staff"):
            return PrescriptionMed.objects.filter(staff_id=user.staff)
        return PrescriptionMed.objects.all()


# -------------------------
# PrescriptionLab ViewSet
# -------------------------
class PrescriptionLabViewSet(NoUpdateDeleteMixin, viewsets.ModelViewSet):
    serializer_class = PrescriptionLabSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "staff"):
            return PrescriptionLab.objects.filter(staff_id=user.staff)
        return PrescriptionLab.objects.all()

