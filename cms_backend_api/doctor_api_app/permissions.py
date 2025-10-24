# doctor/permissions.py
from rest_framework.permissions import BasePermission


class IsAssignedDoctor(BasePermission):
    """
    Allow access only to doctors consulting their own assigned patients.
    """

    def has_permission(self, request, view):
        """
        View-level check — ensures only authenticated doctors can access.
        """
        user = request.user
        return user.is_authenticated and hasattr(user, "staff_profile") and getattr(user, "role", None) == "DOC"

    def has_object_permission(self, request, view, obj):
        """
        Object-level check — ensures that the doctor only accesses
        consultations or prescriptions they are assigned to.
        """
        user = request.user
        staff = getattr(user, "staff_profile", None)
        if not staff:
            return False

        # Case 1: ConsultationNotes object
        if hasattr(obj, "appointment_id"):
            return obj.appointment_id.staff == staff

        # Case 2: PrescriptionMed or PrescriptionLab
        if hasattr(obj, "consultation_id") and hasattr(obj.consultation_id, "appointment_id"):
            return obj.consultation_id.appointment_id.staff == staff

        # Case 3: If none of the above match, deny access
        return False
