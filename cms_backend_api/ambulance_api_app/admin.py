from django.contrib import admin
from .models import Ambulance, AmbulanceRequest


@admin.register(Ambulance)
class AmbulanceAdmin(admin.ModelAdmin):
    list_display = ('vehicle_no', 'driver', 'status')
    list_filter = ('status',)
    search_fields = ('vehicle_no', 'driver__name')


@admin.register(AmbulanceRequest)
class AmbulanceRequestAdmin(admin.ModelAdmin):
    list_display = (
        'request_id', 'pickup_location', 'destination',
        'status', 'created_by', 'assigned_driver', 'assigned_ambulance', 'completed_time'
    )
    list_filter = ('status',)
    search_fields = ('pickup_location', 'destination', 'patient_id')
