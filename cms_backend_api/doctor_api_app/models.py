from django.db import models
from receptionist_api_app.models import Appointment
from admin_api_app.models import Staff
from pharmacist_api_app.models import Medicine
from labtech_api_app.models import LabTest      


# ------------------ CONSULTATION NOTES ------------------

class ConsultationNotes(models.Model):
    consultation_auto_id = models.AutoField(primary_key=True)
    consultation_id = models.CharField(max_length=100, unique=True, blank=True)  # e.g., CONS001
    appointment_id = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="consultations",null=True, blank=True
    )
    staff_id = models.ForeignKey(  # doctor
        Staff, on_delete=models.CASCADE, related_name="doctor_consultations"
    )
    symptoms = models.TextField()
    diagnosis = models.TextField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Consultation {self.consultation_id} | "
            f"Patient: {self.appointment_id.patient_id.patient_name} "
            f"({self.appointment_id.patient_id.patient_id}) | "
            f"Doctor: {self.staff_id.name} | "
            f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

    def save(self, *args, **kwargs):
        if not self.consultation_id or str(self.consultation_id).strip() == "":
            last = ConsultationNotes.objects.order_by("consultation_auto_id").last()
            if last and last.consultation_id.startswith("CONS"):
                last_num = int(last.consultation_id.replace("CONS", ""))
                self.consultation_id = f"CONS{last_num+1:03d}"
            else:
                self.consultation_id = "CONS001"
        super().save(*args, **kwargs)


# ------------------ PRESCRIPTION MEDICINES ------------------

class PrescriptionMed(models.Model):
    prescription_auto_id = models.AutoField(primary_key=True)
    prescription_med_id = models.CharField(max_length=100, unique=True, blank=True  )
    consultation_id = models.OneToOneField(
        ConsultationNotes, on_delete=models.CASCADE, related_name="prescriptions_med"
    )
    
    staff_id = models.ForeignKey(
        Staff, on_delete=models.CASCADE, related_name="doctor_prescriptions_med"
    )
    medicines = models.ManyToManyField(
        "pharmacist_api_app.Medicine",
        through="PrescriptionMedDetail",
        related_name="medicine_prescriptions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        patient = self.consultation_id.appointment_id.patient_id
        return (
            f"Prescription {self.prescription_med_id} | "
            f"Patient: {patient.patient_name} ({patient.patient_id}) | "
            f"Medicines: {self.medicines.count()} | "
            f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

    def save(self, *args, **kwargs):
        # Auto-generate PrescriptionMed ID
        if not self.prescription_med_id or self.prescription_med_id.strip() == "":
            last = PrescriptionMed.objects.order_by("prescription_auto_id").last()
            if last and last.prescription_med_id and last.prescription_med_id.startswith("PMED"):
                last_num = int(last.prescription_med_id.replace("PMED", ""))
                self.prescription_med_id = f"PMED{last_num+1:03d}"
            else:
                self.prescription_med_id = "PMED001"
        super().save(*args, **kwargs)


class PrescriptionMedDetail(models.Model):
    prescription = models.ForeignKey(PrescriptionMed, on_delete=models.CASCADE)
    medicine = models.ForeignKey("pharmacist_api_app.Medicine", on_delete=models.CASCADE, blank=True, null=True)
    custom_medicine_name = models.CharField(max_length=200, blank=True, null=True, help_text="Custom medicine not in database")
    dosage = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(blank=True, null=True)
    frequency = models.CharField(max_length=100, help_text="e.g., Twice a day", blank=True, null=True)
    duration = models.CharField(max_length=100, help_text="e.g., 5 days", blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.prescription.prescription_med_id}"


# ------------------ PRESCRIPTION LAB TESTS ------------------

class PrescriptionLab(models.Model):
    prescription_lab_auto_id = models.AutoField(primary_key=True)
    prescription_lab_id = models.CharField(max_length=100, unique=True, blank=True)
    consultation_id = models.OneToOneField(
        ConsultationNotes, on_delete=models.CASCADE, related_name="prescriptions_lab"
    )
   
    staff_id = models.ForeignKey(
        Staff, on_delete=models.CASCADE, related_name="doctor_prescriptions_lab"
    )
    lab_tests = models.ManyToManyField(
        "labtech_api_app.LabTest",
        through="PrescriptionLabDetail",
        related_name="lab_prescriptions"
    )
    priority = models.CharField(
        max_length=20,
        choices=[("routine", "Routine"), ("urgent", "Urgent")],
        default="routine"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        patient = self.consultation_id.appointment_id.patient_id
        return (
            f"Lab Prescription {self.prescription_lab_id} | "
            f"Patient: {patient.patient_name} ({patient.patient_id}) | "
            f"Tests: {self.lab_tests.count()} | "
            f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

    def save(self, *args, **kwargs):
        # Auto-generate PrescriptionLab ID
        if not self.prescription_lab_id or self.prescription_lab_id.strip() == "":
            last = PrescriptionLab.objects.order_by("prescription_lab_auto_id").last()
            if last and last.prescription_lab_id and last.prescription_lab_id.startswith("PLAB"):
                last_num = int(last.prescription_lab_id.replace("PLAB", ""))
                self.prescription_lab_id = f"PLAB{last_num+1:03d}"
            else:
                self.prescription_lab_id = "PLAB001"
        super().save(*args, **kwargs)


class PrescriptionLabDetail(models.Model):
    prescription = models.ForeignKey(PrescriptionLab, on_delete=models.CASCADE)
    lab_test = models.ForeignKey("labtech_api_app.LabTest", on_delete=models.CASCADE, blank=True, null=True)
    custom_lab_test_name = models.CharField(max_length=200, blank=True, null=True, help_text="Custom lab test not in database")
    instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.prescription.prescription_lab_id}"
