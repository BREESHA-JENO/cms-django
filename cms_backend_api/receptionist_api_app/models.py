from django.db import models
from admin_api_app.models import Staff

def next_code(model, field_name: str, prefix: str) -> str:
    last = model.objects.exclude(**{field_name: ''}).order_by('-pk').first()
    if not last:
        return f'{prefix}001'
    last_code = getattr(last, field_name, '') or ''
    if last_code.startswith(prefix):
        try:
            n = int(last_code.replace(prefix, ''))
        except Exception:
            n = last.pk
    else:
        n = last.pk
    return f'{prefix}{n+1:03d}'

class Patient(models.Model):
    patient_auto_id = models.AutoField(primary_key=True)
    patient_id = models.CharField(max_length=100, unique=True)
    patient_name = models.CharField(max_length=255)
    patient_email = models.EmailField(blank=True)
    patient_age = models.PositiveIntegerField()
    patient_gender = models.CharField(max_length=10)
    patient_blood_group = models.CharField(max_length=5)
    patient_phone = models.CharField(max_length=15)
    patient_address = models.TextField()
    patient_reg_date = models.DateField()
    patient_created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # For soft delete

    def save(self, *args, **kwargs):
        if not self.patient_id or not self.patient_id.strip():
            self.patient_id = next_code(Patient, 'patient_id', 'PAT')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.patient_name}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    appointment_auto_id = models.AutoField(primary_key=True)
    appointment_id = models.CharField(max_length=100, unique=True)
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    appoinment_date = models.DateField()
    appoinment_time = models.TimeField()
    appoinment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    appoinment_created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.appointment_id or not self.appointment_id.strip():
            self.appointment_id = next_code(Appointment, 'appointment_id', 'APP')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.appointment_id} - {self.patient_id.patient_name}"

class RecBilling(models.Model):
    BILLING_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Partially Paid', 'Partially Paid'),
    ]
    rec_bill_id = models.AutoField(primary_key=True)
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    billing_status = models.CharField(max_length=20, choices=BILLING_STATUS_CHOICES, default='Unpaid')
    billing_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Billing {self.rec_bill_id} - {self.patient_id.patient_name}"
