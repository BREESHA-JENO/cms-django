from django.db import models

class Ambulance(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('On Duty', 'On Duty'),
        ('Maintenance', 'Maintenance'),
    ]
    
    ambulance_id = models.AutoField(primary_key=True)
    vehicle_no = models.CharField(max_length=20, unique=True)
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    
    def __str__(self):
        return f"{self.vehicle_no} - {self.driver_name}"


class AmbulanceRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    request_id = models.AutoField(primary_key=True)
    request_time = models.DateTimeField(auto_now_add=True)
    pickup_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    assigned_ambulance = models.ForeignKey(Ambulance, on_delete=models.SET_NULL, null=True, blank=True)
    patient_id = models.CharField(max_length=100, null=True, blank=True)  # Can link to Patient or TempPatient later
    
    def __str__(self):
        return f"Request {self.request_id} - {self.status}"
