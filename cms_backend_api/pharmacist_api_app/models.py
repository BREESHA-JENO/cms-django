from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from receptionist_api_app.models import Patient


class Medicine(models.Model):
    medicine_id = models.AutoField(primary_key=True)
    med_id = models.CharField(max_length=10, unique=True, blank=True)  # Custom MED001
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True, null=True)
    brand_name = models.CharField(max_length=100, blank=True, null=True)
    form = models.CharField(max_length=50, choices=[
        ('Tablet', 'Tablet'),
        ('Syrup', 'Syrup'),
        ('Injection', 'Injection'),
        ('Capsule', 'Capsule'),
        ('Other', 'Other'),
    ])
    strength = models.CharField(max_length=50, blank=True, null=True)  # e.g. 500mg
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.med_id} - {self.name} ({self.strength})"


# Auto-generate MED001, MED002...
@receiver(pre_save, sender=Medicine)
def set_med_id(sender, instance, **kwargs):
    if not instance.med_id:
        last = Medicine.objects.all().order_by('-medicine_id').first()
        if last:
            last_id = int(last.med_id.replace("MED", "")) if last.med_id else 0
        else:
            last_id = 0
        instance.med_id = f"MED{last_id+1:03d}"


class Stock(models.Model):
    stock_id = models.AutoField(primary_key=True)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="stocks")
    batch_number = models.CharField(max_length=50)
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField()
    reorder_level = models.PositiveIntegerField(default=10)  # alert when below this

    @property
    def status(self):
        from datetime import date
        if self.expiry_date < date.today():
            return "Expired"
        elif self.quantity <= self.reorder_level:
            return "Low Stock"
        return "In Stock"

    def __str__(self):
        return f"{self.medicine.name} - Batch {self.batch_number}"

class Prescription(models.Model):
    prescription_id = models.AutoField(primary_key=True)
    doctor = models.ForeignKey("doctor_api_app.DoctorDetails", on_delete=models.CASCADE, related_name="prescriptions")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions")
    date_prescribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription {self.prescription_id} - Patient {self.patient.patient_name}"

class PrescriptionMedicine(models.Model):
    id = models.AutoField(primary_key=True)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="medicines")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="prescriptions")
    dosage = models.CharField(max_length=50)      # e.g. "1 tablet"
    frequency = models.CharField(max_length=50)   # e.g. "Twice daily"
    duration = models.CharField(max_length=50)    # e.g. "5 days"
    quantity_prescribed = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.medicine.name} for {self.prescription.patient.patient_name}"


# ✅ NEW: Medicine Billing
class MedicineBilling(models.Model):
    bill_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medicine_bills")
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True)
    bill_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Bill {self.bill_id} - Patient {self.patient.patient_name}"


class MedicineBillingItem(models.Model):
    id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(MedicineBilling, on_delete=models.CASCADE, related_name="items")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity} ({self.bill.patient.patient_name})"

    class Meta:
        verbose_name = "Medicine Billing Item"
        verbose_name_plural = "Medicine Billing Items"