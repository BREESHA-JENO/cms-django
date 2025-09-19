from django import timezone
from django.db import models
from doctor_api_app.models import PrescriptionLab

# Create your models here.

class LabTestCategory(models.Model):
    CategoryId = models.AutoField(primary_key=True)
    CategoryName = models.CharField(max_length=100, unique=True)


    def __str__(self):
        return self.CategoryName

class LabTest(models.Model):
    Id = models.AutoField(primary_key=True)
    LabTestId = models.CharField(max_length=10, unique=True, editable=False)
    LabTestName = models.CharField(max_length=100)
    CategoryId = models.ForeignKey(LabTestCategory, on_delete=models.CASCADE)
    Rate = models.DecimalField(max_digits=10, decimal_places=2)
    Min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    Max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    Is_Active = models.BooleanField(default=True)
    Created_On = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.LabTestId:
            last_test = LabTest.objects.order_by("-Id").first()
            if last_test:
                last_num = int(last_test.LabTestId.replace("TEST",""))
                new_num = last_num+1
            else:
                new_num = 1
            self.LabTestId = f"TEST{new_num:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.LabTestId} --- {self.LabTestName}"
    

class LabResult(models.Model):
    ResultId = models.AutoField(primary_key=True)
    TestId = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    Status = models.CharField(max_length=50, choices= [("Pending", "pending"), ("Completed", "completed")])
    LabPrescriptionId = models.ForeignKey(PrescriptionLab, on_delete=models.CASCADE)
    result_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Result: {self.ResultId} --- {self.TestId.LabTestName}"
    
class LabBilling(models.Model):
    BillId = models.AutoField(primary_key=True)
    LabPrescriptionId = models.ForeignKey(PrescriptionLab, on_delete=models.CASCADE)
    Amount = models.DecimalField(max_digits=10, decimal_places=2)
    BillingDate = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Bill: {self.BillId} --- {self.Amount}"