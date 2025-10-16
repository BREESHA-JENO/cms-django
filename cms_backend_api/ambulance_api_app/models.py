from django.db import models
from admin_api_app.models import Staff

class Ambulance(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('On Duty', 'On Duty'),
        ('Maintenance', 'Maintenance'),
    ]
    
    ambulance_id = models.AutoField(primary_key=True)
    vehicle_no = models.CharField(max_length=20, unique=True)
    driver = models.OneToOneField(
        Staff,
        on_delete=models.CASCADE,
        limit_choices_to={'user__role': 'AMB'},
        related_name='ambulance_driver'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    
    def __str__(self):
        return f"{self.vehicle_no} - {self.driver.name}"



from admin_api_app.models import Staff

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

    created_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ambulance_requests_created',
        limit_choices_to={'user__role': 'REC'}  # receptionist
    )

    assigned_driver = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ambulance_requests_assigned',
        limit_choices_to={'user__role': 'AMB'}
    )

    assigned_ambulance = models.ForeignKey(
        Ambulance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests'
    )

    patient_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Request {self.request_id} - {self.status}"

