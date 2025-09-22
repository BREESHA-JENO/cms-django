from django.db import models

class Patient(models.Model):
    patient_auto_id = models.AutoField(primary_key=True)
    patient_id = models.CharField(max_length=100, unique=True)
    patient_name = models.CharField(max_length=255)
    patinet_email = models.EmailField()
    patient_age = models.PositiveIntegerField()
    patient_gender = models.CharField(max_length=10)
    patient_blood_group = models.CharField(max_length=5)
    patient_phone = models.IntegerField(max_length=15)
    patient_address = models.TextField()
    patient_reg_date = models.DateField()
    patient_created_at = models.DateTimeField(auto_now_add=True)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    appointment_auto_id = models.AutoField(primary_key=True)
    appointment_id = models.CharField(max_length=100, unique=True)
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=100)
    appoinment_date = models.DateField()
    appoinment_time = models.TimeField()
    appoinment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    appoinment_created_at = models.DateTimeField(auto_now_add=True)

class RecBilling(models.Model):
    BILLING_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
    ]
    rec_bill_id = models.AutoField(primary_key=True)
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=100)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    billing_status = models.CharField(max_length=20, choices=BILLING_STATUS_CHOICES, default='Unpaid')
    billing_created_at = models.DateTimeField(auto_now_add=True)
