
from django.db import models
from receptionist_api_app.models import appointments
from pharmacist_api_app.models import pharmacist_medicine
from labtech_api_app.models import lab_tests
from admin_api_app.models import staff


class ConsultationNotes(models.Model):
    consultation_auto_id = models.AutoField(primary_key=True)
    consultation_id = models.CharField(max_length=100, unique=True)
    appointment_id = models.ForeignKey(appointments, on_delete=models.CASCADE, related_name="consultations")
    staff_id = models.ForeignKey(staff, on_delete=models.CASCADE, related_name="doctor_consultations")  # doctor
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
            f"Doctor: {self.staff_id.staff_name} | "
            f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        
    def save(self, *args, **kwargs):
        if not self.consultation_id:
            last = ConsultationNotes.objects.all().order_by("consultation_auto_id").last()
            if last:
                last_num = int(last.consultation_id.replace("CONS", ""))
                self.consultation_id = f"CONS{last_num+1:03d}"
            else:
                self.consultation_id = "CONS001"
        super().save(*args, **kwargs)


# ------------------ PRESCRIPTION MEDICINES ------------------

class PrescriptionMed(models.Model):
    prescription_auto_id = models.AutoField(primary_key=True)
    prescription_med_id = models.CharField(max_length=100, unique=True)
    consultation_id = models.ForeignKey(ConsultationNotes, on_delete=models.CASCADE, related_name="prescriptions_med")
    appointment_id = models.ForeignKey(appointments, on_delete=models.CASCADE, related_name="prescriptions_med")
    staff_id = models.ForeignKey(staff, on_delete=models.CASCADE, related_name="doctor_prescriptions_med")
    medicines = models.ManyToManyField(
        pharmacist_medicine,
        through="PrescriptionMedicineDetail",
        related_name="medicine_prescriptions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        patient = self.appointment_id.patient_id
        med_count = self.medicines.count()
        return (
            f"Prescription {self.prescription_med_id} | "
            f"Patient: {patient.patient_name} ({patient.patient_id}) | "
            f"Medicines: {med_count} | "
            f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        
    def save(self, *args, **kwargs):
        if not self.prescription_med_id:
            last = PrescriptionMed.objects.all().order_by("prescription_auto_id").last()
            if last:
                last_num = int(last.prescription_med_id.replace("PMED", ""))
                self.prescription_med_id = f"PMED{last_num+1:03d}"
            else:
                self.prescription_med_id = "PMED001"
        super().save(*args, **kwargs)


class PrescriptionMedDetail(models.Model):
    prescription = models.ForeignKey(PrescriptionMed, on_delete=models.CASCADE)
    medicine = models.ForeignKey(pharmacist_medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=200)
    quantity = models.IntegerField()
    instructions = models.TextField(blank=True, null=True)
    


# ------------------ PRESCRIPTION LAB TESTS ------------------

class PrescriptionLab(models.Model):
    prescription_lab_auto_id = models.AutoField(primary_key=True)
    prescription_lab_id = models.CharField(max_length=100, unique=True)
    consultation_id = models.ForeignKey(ConsultationNotes, on_delete=models.CASCADE, related_name="prescriptions_lab")
    appointment_id = models.ForeignKey(appointments, on_delete=models.CASCADE, related_name="prescriptions_lab")
    staff_id = models.ForeignKey(staff, on_delete=models.CASCADE, related_name="doctor_prescriptions_lab")
    lab_tests = models.ManyToManyField(
        lab_tests,
        through="PrescriptionLabDetail",
        related_name="lab_prescriptions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        patient = self.appointment_id.patient_id
        test_count = self.lab_tests.count()
        return (
            f"Lab Prescription {self.prescription_lab_id} | "
            f"Patient: {patient.patient_name} ({patient.patient_id}) | "
            f"Tests: {test_count} | "
            f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        
    def save(self, *args, **kwargs):
        if not self.prescription_lab_id:
            last = PrescriptionLab.objects.all().order_by("prescription_lab_auto_id").last()
            if last:
                last_num = int(last.prescription_lab_id.replace("PLAB", ""))
                self.prescription_lab_id = f"PLAB{last_num+1:03d}"
            else:
                self.prescription_lab_id = "PLAB001"
        super().save(*args, **kwargs)


class PrescriptionLabDetail(models.Model):
    prescription = models.ForeignKey(PrescriptionLab, on_delete=models.CASCADE)
    lab_test = models.ForeignKey(lab_tests, on_delete=models.CASCADE)
    instructions = models.TextField(blank=True, null=True)
