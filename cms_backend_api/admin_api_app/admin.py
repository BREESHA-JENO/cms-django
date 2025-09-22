from django.contrib import admin

# Register your models here.
from .models import Staff, Specialization, DoctorDetails, WorkingDay, DoctorWorkingSchedule
admin.site.register(Staff)
admin.site.register(Specialization)
admin.site.register(DoctorDetails)
admin.site.register(WorkingDay)
admin.site.register(DoctorWorkingSchedule)