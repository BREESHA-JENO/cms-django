from django.contrib import admin
from .models import Patient,RecBilling,Appointment

# Register your models here.

admin.site.register(Patient)
admin.site.register(RecBilling)
admin.site.register(Appointment)