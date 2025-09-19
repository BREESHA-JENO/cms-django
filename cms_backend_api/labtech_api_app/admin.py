from django.contrib import admin

# Register your models here.
from .models import LabTestCategory, LabTest, LabBilling, LabResult
admin.site.register(LabTestCategory)
admin.site.register(LabTest)
admin.site.register(LabBilling)
admin.site.register(LabResult)