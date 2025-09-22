from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    ConsultationNotes,
    PrescriptionMed,
    PrescriptionMedDetail,
    PrescriptionLab,
    PrescriptionLabDetail,
)

admin.site.register(ConsultationNotes)
admin.site.register(PrescriptionMed)
admin.site.register(PrescriptionMedDetail)
admin.site.register(PrescriptionLab)
admin.site.register(PrescriptionLabDetail)
