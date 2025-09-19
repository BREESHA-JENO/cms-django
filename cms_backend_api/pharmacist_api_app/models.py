from django.db import models


# ------------------ MEDICINE MASTER ------------------

class Medicine(models.Model):
    med_auto_id = models.AutoField(primary_key=True)
    med_id = models.CharField(max_length=10, unique=True, blank=True)  # MED001
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.med_id:
            last = Medicine.objects.order_by("med_auto_id").last()
            if last:
                last_num = int(last.med_id.replace("MED", ""))
                self.med_id = f"MED{last_num+1:03d}"
            else:
                self.med_id = "MED001"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.med_id} - {self.name}"


# ------------------ STOCK ------------------

class Stock(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="stocks")
    quantity = models.IntegerField()
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.medicine.name} - {self.quantity} units"


# ------------------ PHARMACIST PRESCRIPTION (LINKS TO DOCTOR PRESCRIPTION) ------------------

class Prescription(models.Model):
    prescription = models.OneToOneField(
        "doctor_api_app.PrescriptionMed",
        on_delete=models.CASCADE,
        related_name="pharmacy_record"
    )
    dispensed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pharmacy Prescription for {self.prescription.prescription_med_id}"


# ------------------ MEDICINE BILLING ------------------

class MedicineBilling(models.Model):
    bill_auto_id = models.AutoField(primary_key=True)
    bill_id = models.CharField(max_length=10, unique=True, blank=True)  # BILL001
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="billings"
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="billings")
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    billed_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.bill_id:
            last = MedicineBilling.objects.order_by("bill_auto_id").last()
            if last:
                last_num = int(last.bill_id.replace("BILL", ""))
                self.bill_id = f"BILL{last_num+1:03d}"
            else:
                self.bill_id = "BILL001"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill {self.bill_id} - {self.medicine.name}"
