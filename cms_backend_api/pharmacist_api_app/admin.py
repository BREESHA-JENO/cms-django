from django.contrib import admin

# Register your models here.
from .models import Medicine, Stock, MedicineBilling, MedicineBillingItem, Prescription, PrescriptionMedicine
admin.site.register(Medicine)
admin.site.register(Stock)
admin.site.register(MedicineBilling)
admin.site.register(MedicineBillingItem)
admin.site.register(Prescription)
admin.site.register(PrescriptionMedicine)