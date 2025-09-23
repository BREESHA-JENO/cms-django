# receptionist_api_app/admin.py
from django.contrib import admin
from django import forms
from .models import Patient, Appointment, RecBilling

class PatientAdminForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'
        widgets = {
            'patient_reg_date': forms.DateInput(attrs={'type': 'date'}),
        }

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    form = PatientAdminForm
    list_display = ('patient_id', 'patient_name', 'patient_email', 'patient_age', 
                   'patient_gender', 'patient_blood_group', 'patient_phone', 
                   'patient_reg_date', 'patient_created_at')
    list_filter = ('patient_gender', 'patient_blood_group', 'patient_reg_date')
    search_fields = ('patient_id', 'patient_name', 'patient_email', 'patient_phone')
    readonly_fields = ('patient_id', 'patient_created_at')
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_id', 'patient_name', 'patient_email', 'patient_age',
                      'patient_gender', 'patient_blood_group')
        }),
        ('Contact Information', {
            'fields': ('patient_phone', 'patient_address')
        }),
        ('Registration Details', {
            'fields': ('patient_reg_date', 'patient_created_at')
        }),
    )

class AppointmentAdminForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        widgets = {
            'appoinment_date': forms.DateInput(attrs={'type': 'date'}),
            'appoinment_time': forms.TimeInput(attrs={'type': 'time'}),
        }

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentAdminForm
    list_display = ('appointment_id', 'patient_info', 'staff_info', 'appoinment_date', 
                   'appoinment_time', 'appoinment_status', 'appoinment_created_at')
    list_filter = ('appoinment_status', 'appoinment_date', 'staff')
    search_fields = ('appointment_id', 'patient_id__patient_name', 'staff__staff_name')
    readonly_fields = ('appointment_id', 'appoinment_created_at')
    fieldsets = (
        ('Appointment Details', {
            'fields': ('appointment_id', 'patient_id', 'staff', 
                      'appoinment_date', 'appoinment_time', 'appoinment_status')
        }),
        ('System Information', {
            'fields': ('appoinment_created_at',)
        }),
    )
    
    def patient_info(self, obj):
        return f"{obj.patient_id.patient_id} - {obj.patient_id.patient_name}"
    patient_info.short_description = 'Patient'
    
    def staff_info(self, obj):
        return obj.staff.staff_name
    staff_info.short_description = 'Staff'

@admin.register(RecBilling)
class RecBillingAdmin(admin.ModelAdmin):
    list_display = ('rec_bill_id', 'patient_info', 'staff_info', 'consultation_fee', 
                   'billing_status', 'billing_created_at')
    list_filter = ('billing_status', 'billing_created_at')
    search_fields = ('patient_id__patient_name', 'staff__staff_name')
    readonly_fields = ('billing_created_at',)
    fieldsets = (
        ('Billing Information', {
            'fields': ('patient_id', 'staff', 'consultation_fee', 'billing_status')
        }),
        ('System Information', {
            'fields': ('billing_created_at',)
        }),
    )
    
    def patient_info(self, obj):
        return f"{obj.patient_id.patient_id} - {obj.patient_id.patient_name}"
    patient_info.short_description = 'Patient'
    
    def staff_info(self, obj):
        return obj.staff.staff_name
    staff_info.short_description = 'Staff'