from django.db import models
from Authentication.models import User
from django.core.exceptions import ValidationError


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
    date_of_joining = models.DateField(auto_now_add=True)
    address = models.TextField()

    profile_image = models.ImageField(upload_to='staff_profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        if not self.staff_id:
            prefix_map = {
                'ADMIN': 'AD',
                'REC': 'REC',
                'DOC': 'DOC',
                'LAB': 'LAB',
                'PHARM': 'PH',
                'AMB': 'AMB',
            }
            prefix = prefix_map.get(self.user.role, "ST")
            count = Staff.objects.filter(user__role=self.user.role).count() + 1
            self.staff_id = f"{prefix}{count:03d}"  # e.g., DOC001
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff_id} - {self.name}"


class Specialization(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class WorkingDay(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)  # e.g., Monday, Tuesday

    def __str__(self):
        return self.name


class DoctorDetails(models.Model):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name="doctor_details")
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name="doctors")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.staff.name} - {self.specialization.name}"

    class Meta:
        verbose_name = "Doctor Detail"
        verbose_name_plural = "Doctor Details"


class DoctorWorkingSchedule(models.Model):
    doctor = models.ForeignKey(DoctorDetails, on_delete=models.CASCADE, related_name="schedules")
    day = models.ForeignKey(WorkingDay, on_delete=models.CASCADE, related_name="schedules")
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")

        # Check overlapping shifts
        overlapping = DoctorWorkingSchedule.objects.filter(
            doctor=self.doctor,
            day=self.day
        ).exclude(pk=self.pk).filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )
        if overlapping.exists():
            raise ValidationError("Shift overlaps with an existing schedule")


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("doctor", "day", "start_time", "end_time")

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="leaves")
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.name} - {self.status}"

class ForgotPasswordRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="forgot_password_requests")
    reason = models.TextField(blank=True, null=True)  # optional reason/message from staff
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Password Reset Request - {self.staff.name} ({self.status})"
