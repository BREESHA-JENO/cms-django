from django.db import models
from Authentication.models import User

class Staff(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.CharField(max_length=10, unique=True, blank=True)  # AD001, DOC001 etc
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")

    name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    blood_group = models.CharField(max_length=5)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    date_of_joining = models.DateField()
    address = models.TextField()

    def save(self, *args, **kwargs):
        if not self.staff_id:
            prefix_map = {
                'ADMIN': 'AD',
                'REC': 'REC',
                'DOC': 'DOC',
                'LAB': 'LAB',
                'PHARM': 'PH',
            }
            prefix = prefix_map.get(self.user.role, "ST")
            count = Staff.objects.filter(user__role=self.user.role).count() + 1
            self.staff_id = f"{prefix}{count:03d}"  # e.g., DOC001
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff_id} - {self.name}"


class DoctorDetails(models.Model):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name="doctor_details")
    specialization = models.CharField(max_length=100)
    working_days = models.CharField(max_length=50)   # e.g., Mon-Fri
    working_hours = models.CharField(max_length=50)  # e.g., 10AM-5PM
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.staff.name} - {self.specialization}"
