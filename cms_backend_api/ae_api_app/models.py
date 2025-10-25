from django.db import models

# Temporary Patient (unknown/unconscious)
class TempPatient(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Merged', 'Merged'),
        ('Deceased', 'Deceased'),
    ]

    temp_patient_id = models.AutoField(primary_key=True)
    temp_patient_code = models.CharField(max_length=10, unique=True, editable=False)
    name = models.CharField(max_length=255, default='Unknown')
    approx_age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(blank=True)
    identification_marks = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.temp_patient_code:
            last_patient = TempPatient.objects.order_by('-temp_patient_id').first()
            next_id = 1 if not last_patient else last_patient.temp_patient_id + 1
            self.temp_patient_code = f"TP{next_id:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.temp_patient_code} - {self.name}"


# Accident & Emergency Case
class AECase(models.Model):
    TRIAGE_CHOICES = [
        ('Critical', 'Critical'),
        ('Serious', 'Serious'),
        ('Stable', 'Stable'),
    ]
    STATUS_CHOICES = [
        ('Under Treatment', 'Under Treatment'),
        ('Admitted', 'Admitted'),
        ('Discharged', 'Discharged'),
        ('Deceased', 'Deceased'),
    ]

    ae_case_id = models.AutoField(primary_key=True)
    patient_type = models.CharField(max_length=20, choices=[('Permanent', 'Permanent'), ('Temporary', 'Temporary')])
    patient = models.ForeignKey('receptionist_api_app.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    temp_patient = models.ForeignKey('TempPatient', on_delete=models.SET_NULL, null=True, blank=True)
    triage_level = models.CharField(max_length=20, choices=TRIAGE_CHOICES)
    brought_by = models.CharField(max_length=50, blank=True)
    ambulance = models.ForeignKey('ambulance_api_app.Ambulance', on_delete=models.SET_NULL, null=True, blank=True)
    arrival_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Under Treatment')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"AECase {self.ae_case_id} - {self.patient or self.temp_patient}"


# Emergency Treatment
class EmergencyTreatment(models.Model):
    STATUS_CHOICES = [
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    ]

    treatment_id = models.AutoField(primary_key=True)
    ae_case = models.ForeignKey('AECase', on_delete=models.CASCADE)
    doctor = models.ForeignKey('admin_api_app.Staff', on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.TextField(blank=True)
    medicine_list = models.TextField(blank=True)
    lab_tests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ongoing')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Treatment {self.treatment_id} - AECase {self.ae_case.ae_case_id}"
