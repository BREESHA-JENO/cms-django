from django.contrib import admin
from .models import Medicine, Stock, Prescription, MedicineBilling

admin.site.register(Medicine)
admin.site.register(Stock)
admin.site.register(Prescription)
admin.site.register(MedicineBilling)
