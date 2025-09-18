from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('REC', 'Receptionist'),
        ('DOC', 'Doctor'),
        ('LAB', 'Lab Technician'),
        ('PHARM', 'Pharmacist'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='ADMIN')
